"""Main entry point for the Review Board installer.

Version Added:
    1.0
"""

# NOTE: This file must be syntactically compatible with Python 3.7+.
from __future__ import annotations

import argparse
import os
import sys
from gettext import gettext as _
from typing import Dict, List, Optional, TYPE_CHECKING, Tuple

from rbinstall import get_version_string
from rbinstall.errors import InstallerError
from rbinstall.process import debug
from rbinstall.pypi import get_package_version_info
from rbinstall.state import get_system_info
from rbinstall.ui import get_console, init_console
from rbinstall.wizard import start_wizard

if TYPE_CHECKING:
    from rbinstall.state import InstallState, SystemInfo
    from rbinstall.pypi import PackageVersionInfo


def parse_options(
    argv: List[str],
) -> argparse.Namespace:
    """Parse the command line arguments.

    This builds the argument parser and then parses the provided command
    line arguments.

    Version Added:
        1.0

    Args:
        argv (list of str):
            The command line arguments to parse.

    Returns:
        argparse.Namespace:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(prog='rbinstall')
    parser.add_argument(
        '--version',
        action='version',
        version='rbinstall %s' % get_version_string(),
        help=_('Show the version of the Review Board installer.'))
    parser.add_argument(
        '--no-color',
        action='store_false',
        default=(os.environ.get('RBINSTALL_COLOR') != '0'),
        dest='color',
        help=_(
            'Disable color output in the terminal. You can also set '
            '$RBINSTALL_COLOR=0.'
        ))
    parser.add_argument(
        '--noinput',
        action='store_false',
        dest='interactive',
        default=(os.environ.get('RBINSTALL_INTERACTIVE') != '0'),
        help=_(
            'Run without prompting for any questions. This allows for '
            'unattended installs. You can also set $RBINSTALL_INTERACTIVE=0.'
        ))
    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=(os.environ.get('RBINSTALL_DRY_RUN') == '1'),
        help=_(
            'Whether to perform a dry-run of the installation. No '
            'installation commands will actually be run. You can also set '
            '$RBINSTALL_DRY_RUN=1.'
        ))
    parser.add_argument(
        '--debug',
        action='store_true',
        dest='debug',
        default=(os.environ.get('RBINSTALL_DEBUG') == '1'),
        help=_(
            'Run with additional debug information. You can also set '
            '$RBINSTALL_DEBUG=1.'
        ))
    parser.add_argument(
        '--install-path',
        metavar='PATH',
        default=os.path.join('/', 'opt', 'reviewboard'),
        help=_('The location for the Review Board install.'))
    parser.add_argument(
        '--create-sitedir',
        action='store_true',
        default=True,
        help=_(
            'Create a site directory after Review Board is installed. This '
            'is ignored for unattended installs (--noinput).'
        ))
    parser.add_argument(
        '--no-create-sitedir',
        action='store_false',
        default=True,
        help=_(
            "Don't create a site directory after Review Board is installed. "
            "This is always set for unattended installs (--noinput)."
        ))
    parser.add_argument(
        '--sitedir-path',
        metavar='PATH',
        default=os.path.join('/', 'var', 'www', 'reviewboard'),
        help=_(
            'The location for a Review Board site directory, if creating one.'
        ))
    parser.add_argument(
        '--no-install-powerpack',
        action='store_false',
        dest='install_powerpack',
        default=True,
        help=_('Disable installing Power Pack.'))
    parser.add_argument(
        '--no-install-reviewbot-extension',
        action='store_false',
        dest='install_reviewbot_extension',
        default=True,
        help=_('Disable installing the Review Bot extension.'))
    parser.add_argument(
        '--no-install-reviewbot-worker',
        action='store_false',
        dest='install_reviewbot_worker',
        default=True,
        help=_('Disable installing the Review Bot worker.'))
    parser.add_argument(
        '--reviewboard-version',
        metavar='VERSION_OR_SPECIFIER',
        default='latest',
        help=_('The specific version of Review Board to install, or a '
               'Python package version specifier (e.g., "~=6.0")'))
    parser.add_argument(
        '--powerpack-version',
        metavar='VERSION_OR_SPECIFIER',
        default='latest',
        help=_('The specific version of Power Pack to install, or a '
               'Python package version specifier (e.g., "~=6.0")'))
    parser.add_argument(
        '--reviewbot-extension-version',
        metavar='VERSION_OR_SPECIFIER',
        default='latest',
        help=_('The specific version of the Review Bot extension to install, '
               'or a Python package version specifier (e.g., "~=6.0")'))
    parser.add_argument(
        '--reviewbot-worker-version',
        metavar='VERSION_OR_SPECIFIER',
        default='latest',
        help=_('The specific version of the Review Bot worker to install, '
               'or a Python package version specifier (e.g., "~=6.0")'))

    return parser.parse_args(argv)


def get_package_versions(
    *,
    system_info: SystemInfo,
    options: argparse.Namespace,
) -> Dict[str, Optional[PackageVersionInfo]]:
    """Return the versions to use for each Review Board package.

    This will look up the latest/requested versions on PyPI based on the
    options provided to the installer, building a map between package names
    and fetched version information.

    Version Added:
        1.0

    Args:
        system_info (rbinstall.state.SystemInfo):
            Information on the target system.

        options (argparse.Namespace):
            The parsed commadn line arguments.

    Raises:
        rbinstall.errors.InstallerError:
            There was an issue fetching package version information.
    """
    package_candidates: List[Tuple[str, bool, str]] = [
        ('ReviewBoard',
         True,
         options.reviewboard_version),
        ('ReviewBoardPowerPack',
         options.install_powerpack,
         options.powerpack_version),
        ('reviewbot-extension',
         options.install_reviewbot_extension,
         options.reviewbot_extension_version),
        ('reviewbot-worker',
         options.install_reviewbot_worker,
         options.reviewbot_worker_version),
    ]

    package_versions: Dict[str, Optional[PackageVersionInfo]] = {}

    for package_name, install, target_version in package_candidates:
        if install:
            version_info = get_package_version_info(
                system_info=system_info,
                package_name=package_name,
                target_version=target_version)

            if version_info is None:
                raise InstallerError(
                    _('No compatible version of %(package_name)s could '
                      'be found on this system. You may need to install '
                      'on a newer system with a newer version of Python.')
                    % {
                        'package_name': package_name,
                    })
        else:
            version_info = None

        package_versions[package_name] = version_info

    debug('All package information has been fetched.')

    return package_versions


def main(
    argv: List[str] = sys.argv,
) -> None:
    """Main entry point for the Review Board installer.

    This will parse any command line arguments, set up the initial install
    state, and then invoke the install wizard.

    Version Added:
        1.0

    Args:
        argv (list of str, optional):
            The command line arguments to parse.
    """
    options = parse_options(argv[1:])
    console = get_console()

    try:
        debug('Setting up the installer console support.')

        init_console(allow_color=options.color,
                     allow_interactive=options.interactive)

        if options.interactive and not os.isatty(sys.stdout.fileno()):
            raise InstallerError(_(
                'To run the Review Board installer without an interactive '
                'terminal, please run with --noinput. This will run an '
                'unattended install of Review Board, using defaults.'
            ))

        with console.status(_('Gathering system and package information...')):
            system_info = get_system_info()
            package_versions = get_package_versions(system_info=system_info,
                                                    options=options)

        rb_version_info = package_versions['ReviewBoard']
        assert rb_version_info is not None

        install_state: InstallState = {
            'create_sitedir': options.create_sitedir and options.interactive,
            'dry_run': options.dry_run,
            'install_powerpack': options.install_powerpack,
            'install_reviewbot_extension': options.install_reviewbot_extension,
            'install_reviewbot_worker': options.install_reviewbot_worker,
            'powerpack_version_info': package_versions['ReviewBoardPowerPack'],
            'reviewboard_version_info': rb_version_info,
            'reviewbot_extension_version_info':
                package_versions['reviewbot-extension'],
            'reviewbot_worker_version_info':
                package_versions['reviewbot-worker'],
            'sitedir_path': options.sitedir_path,
            'steps': [],
            'system_info': system_info,
            'unattended_install': not options.interactive,
            'venv_path': options.install_path,
            'venv_pip_exe': '',
            'venv_python_exe': '',
        }

        start_wizard(install_state=install_state)
    except KeyboardInterrupt:
        pass
    except InstallerError as e:
        console.print(e, style='error')
        sys.exit(1)


if __name__ == '__main__':
    main()
