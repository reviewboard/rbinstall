"""UI support for the installer.

Version Added:
    1.0
"""

# NOTE: This file must be syntactically compatible with Python 3.7+.
from __future__ import annotations

import os
import sys

from gettext import gettext as _
from typing import List, Optional, TYPE_CHECKING, Tuple

from rbinstall.errors import InstallerError
from rbinstall.install_methods import run_install_method
from rbinstall.install_steps import get_install_steps
from rbinstall.process import RunCommandError, join_cmdline, run
from rbinstall.ui import (ShellCommand,
                          get_console,
                          print_header,
                          print_key_values,
                          print_note,
                          print_ol,
                          print_paragraphs,
                          print_terms,
                          prompt_confirm,
                          prompt_string,
                          show_progress)

if TYPE_CHECKING:
    from rbinstall.state import InstallState


SUPPORT_LINK = \
    '[link=mailto:support@beanbaginc.com]support@beanbaginc.com[/link]'
SITEDIR_DOCS_LINK = (
    '[link]https://www.reviewboard.org/docs/manual/latest/admin/'
    'installation/creating-sites/[/link]'
)


def _show_install_info_table(
    *,
    install_state: InstallState
) -> None:
    """Show a table of operating system and version information details.

    Version Added:
        1.0

    Args:
        install_state (rbinstall.state.InstallState):
            The Review Board installation state.
    """
    system_info = install_state['system_info']
    rows: List[Tuple[str, str]] = []

    # Add information on the operating system.
    system = system_info['system']

    if system == 'Linux':
        os_key = _('Linux distribution')
        os_name = system_info.get('distro_name') or _('Unknown Distro')
    else:
        os_key = _('Operating system')

        if system == 'Darwin':
            os_name = 'macOS'
        else:
            os_name = system

    rows.append((
        os_key,
        _('%(os_name)s %(os_version)s (%(arch)s)')
        % {
            'arch': system_info['arch'],
            'os_name': os_name,
            'os_version': system_info['version'],
        },
    ))

    # Add information on the system package installer.
    rows.append((
        _('Package installer'),
        system_info['system_install_method'],
    ))

    # Add information on the version of Python.
    python_ver = '%s.%s.%s' % system_info['system_python_version'][:3]
    rows.append((
        _('Python'),
        _('%(python_ver)s (%(python_exe)s)')
        % {
            'python_exe': system_info['system_python_exe'],
            'python_ver': python_ver,
        },
    ))

    # Add information on the package versions.
    for label, version_key in ((_('Review Board'),
                                'reviewboard_version_info'),
                               (_('Power Pack'),
                                'powerpack_version_info'),
                               (_('Review Bot worker'),
                                'reviewbot_worker_version_info'),
                               (_('Review Bot extension'),
                                'reviewbot_extension_version_info')):
        # Ignore typing of the key, since we can't specify that the above
        # are known keys of the dictionary.
        version_info = install_state[version_key]  # type: ignore

        if version_info:
            version = version_info['version']
            latest_version = version_info['latest_version']

            if version_info['is_latest']:
                # This is the latest version of the package.
                version_text = (
                    _('%(version)s ([green]latest[/])')
                    % {
                        'version': version,
                    })
            elif version_info['is_requested']:
                # A specific version was requested, but it's not the latest
                # version.
                version_text = (
                    _('%(version)s ([green]requested[/] ─ latest stable '
                      'version is %(latest_version)s)')
                    % {
                        'latest_version': latest_version,
                        'version': version,
                    })
            else:
                # This is an older version, and is the latest version
                # compatible with this system.
                version_text = (
                    _('%(version)s ([note]latest for Python %(python_ver)s[/]'
                      ' ─ latest stable version is %(latest_version)s)')
                    % {
                        'latest_version': latest_version,
                        'python_ver': python_ver,
                        'version': version,
                    }
                )
        else:
            # This package won't be installed.
            version_text = _('[red]Will not be installed[/]')

        rows.append((label, version_text))

    # List any file paths. As of this writing, only `brew` will be in here,
    # and only if detected while on macOS.
    rows += tuple(system_info.get('paths', {}).items())

    # Render the table of information.
    print_key_values(rows=rows)


def _show_intro(
    install_state: InstallState,
) -> None:
    """Show the introduction for the installation wizard.

    This will provide a summary of the install process, information on the
    current system and target versions, and prompt for confirmation before
    the wizard continues.

    Version Added:
        1.0

    Args:
        install_state (rbinstall.state.InstallState):
            The Review Board installation state.
    """
    console = get_console()

    print_header(_('Welcome to the Review Board installer!'),
                 first=True)

    print_paragraphs([
        _("We'll walk you through installing Review Board on your system. "
          "You'll be asked some questions about your install, and then we'll "
          "take care of installing Review Board for you."),

        _('If you need to exit the installer, press Control-C at any time. '
          'If you need help, contact %(support_link)s.')
        % {
            'support_link': SUPPORT_LINK,
        },

        _("First, let's confirm some details about your system:"),
    ])

    _show_install_info_table(install_state=install_state)

    print_note(_(
        'The version of Python is important! If you need Review Board to use '
        'a different version of Python, you will need to re-run this '
        'installer using that version.'
    ))

    if not prompt_confirm('Does this look correct?', default=True):
        console.print()
        console.print()
        console.print(_(
            '[error]Cancelling the installation.[/] If you need help, you '
            'can contact %(support_link)s.'
        ) % {
            'support_link': SUPPORT_LINK,
        })

        sys.exit(1)


def _show_ask_install_location(
    install_state: InstallState,
) -> None:
    """Show a page asking for the install location.

    This will describe the terms for Installation Directory vs. Site Directory
    and prompt for a suitable installation directory. It will also validate
    that the directory is suitable for a Review Board install.

    Version Added:
        1.0

    Args:
        install_state (rbinstall.state.InstallState):
            The Review Board installation state.
    """
    console = get_console()

    print_header(_('Choose Your Install Location'))

    print_paragraphs(_(
        "There are two directories that you'll need to know about:"
    ))

    print_terms([
        (_('Installation Directory'),
         _("This is where Review Board will be installed. This is a Python "
           "Virtual Environment, which will contain the Review Board Python "
           "packages and executable files. It'll be specific to this "
           "version of Python, so you'll need to re-install if upgrading "
           "to a new version of Python.")),

        (_('Site Directory'),
         _("This is a directory containing configuration, data, file storage, "
           "and more for a specific Review Board website (e.g., "
           "reviews.example.com). One server can host multiple Review Board "
           "sites, each with their own site directory.")),
    ])

    print_paragraphs(
        _("You'll create your Site Directory later. For now, let's figure "
          "out where Review Board will be installed."),
    )

    venv_path: Optional[str] = None

    while not venv_path:
        venv_path = prompt_string(_('Review Board installation directory'),
                                  default=install_state['venv_path'])

        # Check if this path is valid.
        if venv_path and os.path.exists(venv_path):
            has_files = bool(os.listdir(venv_path))

            if has_files:
                console.print()

                if os.path.exists(os.path.join(venv_path, 'bin', 'rb-site')):
                    print_paragraphs(
                        [
                            _("There's already an installation at %(path)s. "
                              "If you are trying to upgrade Review Board, "
                              "exit the installer (press Control-C) and run:")
                            % {
                                'path': venv_path,
                            },

                            ShellCommand(
                                '%s install ReviewBoard==<version>'
                                % os.path.join(venv_path, 'bin', 'pip'),
                            ),
                        ],
                        style='error')
                else:
                    print_paragraphs(
                        [
                            _('You must specify a Review Board installation '
                              'path that does not already exist.'),
                        ],
                        style='error')

                if install_state['unattended_install']:
                    # We can't recover from this.
                    sys.exit(1)

                venv_path = ''

    install_state.update({
        'venv_path': venv_path,
        'venv_pip_exe': os.path.join(venv_path, 'bin', 'pip'),
        'venv_python_exe': os.path.join(venv_path, 'bin', 'python'),
    })


def _show_confirm_install(
    install_state: InstallState,
) -> None:
    """Show a page confirming the user is ready to install Review Board.

    This will show the steps that will be performed and then prompt if the
    user is ready to execute them.

    Version Added:
        1.0

    Args:
        install_state (rbinstall.state.InstallState):
            The Review Board installation state.
    """
    print_header(_('Preparing To Install Review Board'))

    commands: List[List[str]] = []

    install_steps = get_install_steps(install_state=install_state)
    install_state['steps'] = install_steps

    for install_step in install_steps:
        run_install_method(
            install_method=install_step['install_method'],
            install_state=install_state,
            args=install_step.get('state', []),
            run_kwargs={
                'capture_command': commands,
                'dry_run': True,
            })

    print_paragraphs([
        _("We're ready to install Review Board! Let's go over the commands "
          "that will be run:"),
    ] + [
        ShellCommand(join_cmdline(command))
        for command in commands
    ])

    print_paragraphs(_(
        'Please read through this. To cancel installation, press Control-C.'
    ))

    confirm_install: bool = False

    while not confirm_install:
        confirm_install = \
            prompt_confirm(_('Are you ready to install Review Board?'),
                           unattended_default=True)

        if not confirm_install:
            cancel_install = prompt_confirm(_('Do you want to cancel?'))

            if cancel_install:
                sys.exit(0)


def _perform_install(
    install_state: InstallState,
) -> None:
    """Perform the installation.

    This will show progress and stream output as the installation progresses.

    Version Added:
        1.0

    Args:
        install_state (rbinstall.state.InstallState):
            The Review Board installation state.
    """
    console = get_console()
    install_steps = install_state['steps']

    console.print()

    with show_progress() as progress:
        task = progress.add_task(_('Preparing...'),
                                 total=len(install_steps))

        max_name_len = max(
            len(install_step['name'])
            for install_step in install_steps
        )

        for install_step in install_steps:
            step_name = install_step['name']
            name_len = len(step_name)
            progress.update(
                task,
                description=step_name + ' ' * (max_name_len - name_len))

            try:
                run_install_method(
                    install_method=install_step['install_method'],
                    install_state=install_state,
                    args=install_step.get('state', []))
            except InstallerError as e:
                if install_step.get('allow_fail'):
                    progress.console.print(str(e), style='error')
                    progress.console.print(_('Continuing...'), style='error')
                else:
                    raise

            progress.advance(task)

        progress.update(task,
                        description='[progress.complete]%s'
                        % _('Installation is complete!'))


def _show_setup_site_dir(
    install_state: InstallState,
) -> None:
    """Guide the user through a site directory setup.

    This will ask the user whether they're creating a new site or importing
    one, and guide the user.

    Version Added:
        1.0

    Args:
        install_state (rbinstall.state.InstallState):
            The Review Board installation state.
    """
    console = get_console()

    print_header(_('Your Site Directory'))

    print_paragraphs([
        _("If this is your first Review Board install, we'll help you create "
          "your Site Directory now."),

        _("If you have an existing Review Board install you're setting up "
          "on this server, we'll guide you through importing it here."),

        _('We recommend reading through the [bold]Creating a Review Board '
          'Site[/] documentation, which will contain additional information '
          'on creating your database and Site Directory and configuring your '
          'system and web server to use it: %(sitedir_docs_url)s')
        % {
            'sitedir_docs_url': SITEDIR_DOCS_LINK,
        }
    ])

    site_is_new = prompt_confirm(
        _('Is this a brand-new Review Board install?'),
        default=install_state['create_sitedir'])
    install_state['create_sitedir'] = site_is_new

    console.print()
    console.print()

    if site_is_new:
        # The user wants to set up a brand-new Review Board site directory.
        #
        # Find out if we should run the command for them.
        rbsite_bin_path = os.path.join(install_state['venv_path'], 'bin',
                                       'rb-site')

        print_paragraphs([
            _('To create a new Site Directory, run:'),

            ShellCommand(
                '%s install %s'
                % (rbsite_bin_path,
                   os.path.join('/', 'path', 'to', 'sitedir')),
            ),
        ])

        create_site = prompt_confirm(
            _('Do you want to create a Site Directory now?'),
            default=True,
            unattended_default=False)

        console.print()
        console.print()
        print_paragraphs(_(
            'Decide where your Site Directory should be. [note]You cannot '
            'change this later![/] Press Control-C if you want to exit the '
            'installer and set up your Site Directory on your own later.'
        ))

        if create_site:
            sitedir: Optional[str] = ''

            while not sitedir:
                sitedir = prompt_string('Review Board site directory',
                                        default=install_state['sitedir_path'])

            install_state['sitedir_path'] = sitedir

            console.print()
    else:
        print_paragraphs(
            _('To set up an existing Review Board site on this server:')
        )
        print_ol([
            [
                _('Copy (or share) the Site Directory from the old server to '
                  'this server.'),
                '',
                _('You **must** copy this to the **same filesystem path!** '
                  'If the Site Directory was at '
                  '[path]/var/www/reviewboard[/] on '
                  'the old, server, it must be copied to '
                  '[path]/var/www/reviewboard[/] on the new server.'),
            ],
            [
                _('If needed, export the database from the old server and '
                  'import it on this server.'),
                '',
                _("If you don't need to move the database, skip this step.")
            ],
            [
                _("Edit the Site Directory's [path]conf/settings_local.py[/] "
                  "file and update any file paths, hostnames, or IP "
                  "addresses."),
                '',
                _('This is required if you are moving your database to this '
                  'server.')
            ],
            [
                _("Copy over or set up your web server's configuration for "
                  "Review Board.")
            ],
        ])


def _create_sitedir(
    install_state: InstallState,
) -> None:
    """Create a site directory.

    This will start the site directory creation process, creating the
    directories leading up to the site directory and then invoking
    :command:`rb-site install`.

    Version Added:
        1.0

    Args:
        install_state (rbinstall.state.InstallState):
            The Review Board installation state.
    """
    dry_run = install_state['dry_run']

    rbsite_bin_path = os.path.join(install_state['venv_path'], 'bin',
                                   'rb-site')
    sitedir_path = install_state['sitedir_path']

    try:
        os.makedirs(sitedir_path, 0o755,
                    exist_ok=True)

        run([rbsite_bin_path, 'install', sitedir_path],
            dry_run=dry_run,
            raw=True)
        success = os.path.exists(os.path.join(sitedir_path, 'conf',
                                              'settings_local.py'))
    except RunCommandError:
        success = False

    if not success:
        print_paragraphs(
            [
                _('The Site Directory was not created or set up correctly. '
                  'However, [success]Review Board was successfully '
                  'installed![/] You can try to create the Site Directory '
                  'again by running:'),

                ShellCommand(f'{rbsite_bin_path} install {sitedir_path}'),

                _('Refer to the [bold]Creating a Review Board Site[/] '
                  'documentation: %(sitedir_docs_link)s')
                % {
                    'sitedir_docs_link': SITEDIR_DOCS_LINK,
                }
            ],
            style='error')
        sys.exit(1)


def start_wizard(
    *,
    install_state: InstallState,
) -> None:
    """Start the installation wizard.

    This will guide the user through the installation process, collecting
    information and choices and handle the installation and site directory
    creation process.

    Version Added:
        1.0

    Args:
        install_state (rbinstall.state.InstallState):
            The Review Board installation state.
    """
    console = get_console()

    _show_intro(install_state)
    _show_ask_install_location(install_state)
    _show_confirm_install(install_state)
    _perform_install(install_state)
    _show_setup_site_dir(install_state)

    if install_state['create_sitedir']:
        _create_sitedir(install_state)

        console.print()
        console.print(
            _('✅ [success]Congratulations![/] Review Board is successfully '
              'installed and your Site Directory created! [bold]Carefully '
              'follow the instructions above[/], and refer to the '
              '[bold]Creating a Review Board Site[/] documentation to finish '
              'setting up: %(sitedir_docs_link)s')
            % {
                'sitedir_docs_link': SITEDIR_DOCS_LINK,
            }
        )
    else:
        console.print()
        console.print(
            _("✅ [success]Congratulations![/] Review Board is successfully "
              "installed! Once you've imported or created your Site "
              "Directory, you'll be ready to use Review Board. Refer to the "
              "[bold]Creating a Review Board Site[/] documentation: "
              "%(sitedir_docs_link)s")
            % {
                'sitedir_docs_link': SITEDIR_DOCS_LINK,
            }
        )

    console.print()
    console.print(
        _('Contact %(support_link)s if you need assistance.')
        % {
            'support_link': SUPPORT_LINK,
        }
    )
