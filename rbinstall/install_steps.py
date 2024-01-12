"""Steps for installing Review Board.

Version Added:
    1.0
"""

# NOTE: This file must be syntactically compatible with Python 3.7+.
from __future__ import annotations

from gettext import gettext as _
from itertools import chain
from typing import Dict, Generic, List, Set, TYPE_CHECKING, TypeVar, Tuple

from typing_extensions import NotRequired, TypeAlias, TypedDict

from rbinstall.distro_info import PACKAGES
from rbinstall.install_methods import (COMMON_INSTALL_METHODS,
                                       InstallMethodType)
from rbinstall.versioning import parse_version

if TYPE_CHECKING:
    from rbinstall.state import InstallState


_T = TypeVar('_T')


class _InstallStep(Generic[_T], TypedDict):
    """An installation step to execute.

    Version Added:
        1.0
    """

    #: The installation method used.
    install_method: InstallMethodType

    #: The name of this step, for display purposes.
    name: str

    #: Whether this installation step is allowed to fail.
    #:
    #: If allowed to fail, an unsuccessful package installation will not
    #: cause the overall Review Board installation to fail.
    allow_fail: NotRequired[bool]

    #: The method-specific state to execute for this step.
    state: NotRequired[_T]


InstallSteps: TypeAlias = List[_InstallStep]


def get_install_package_steps(
    install_state: InstallState,
    *,
    categories: List[str],
    package_type: str,
    description: str = '',
) -> InstallSteps:
    """Return steps for installing some packages for the target system.

    This will go through the packages available for installation, returning
    installation steps for any entries that match the criteria for the target
    system.

    Version Added:
        1.0

    Args:
        install_state (rbinstall.state.InstallState):
            The state for the installation.

        categories (list of str):
            The list of top-level package categories to consider.

        package_type (str):
            The package type nested within the category.

        description (str, optional):
            An optional description for the steps.

    Returns:
        list of _InstallStep:
        The resulting list of steps.
    """
    packages: Dict[Tuple[InstallMethodType, int], List[str]] = {}
    packages_set: Dict[Tuple[InstallMethodType, int], Set[str]] = {}
    allow_fail_map: Dict[Tuple[InstallMethodType, int], bool] = {}
    setup_commands: List[List[str]] = []
    flags: Set[str] = set()

    system_info = install_state['system_info']
    arch = system_info['arch']
    distro_families = system_info.get('distro_families')
    distro_id = system_info.get('distro_id')
    system = system_info['system']
    system_install_method = system_info['system_install_method']

    supported_install_methods = \
        COMMON_INSTALL_METHODS | {system_install_method}

    # Normalize the Review Board version to install.
    rb_version_info = parse_version(
        install_state['reviewboard_version_info']['version'])

    # Normalize the distro version in use.
    distro_version_info = parse_version(system_info['version'])

    package_candidates = chain.from_iterable(
        PACKAGES[category].get(package_type, [])
        for category in categories
    )

    for i, candidate in enumerate(package_candidates):
        match_info = candidate.get('match', {})

        # Check for a system match.
        if system not in match_info.get('systems', {system}):
            continue

        # Check for an architecture match.
        if arch not in match_info.get('archs', {arch}):
            continue

        # Check that the install method is compatible.
        install_method = candidate.get('install_method',
                                       InstallMethodType.SYSTEM_DEFAULT)

        if install_method == InstallMethodType.SYSTEM_DEFAULT:
            install_method = system_install_method

        if install_method not in supported_install_methods:
            continue

        # Check that at least one of the distro families match.
        match_distro_families = match_info.get('distro_families', set())

        if (distro_families and
            match_distro_families and
            not (match_distro_families & distro_families)):
            continue

        # Check for a distro ID match.
        if (distro_id and
            distro_id not in match_info.get('distro_ids', {distro_id})):
            continue

        # Check for a distro version match.
        version_func = match_info.get('distro_version')

        if version_func is not None and not version_func(distro_version_info):
            continue

        # Check for a Review Board version match.
        version_func = match_info.get('rb_version')

        if version_func is not None and not version_func(rb_version_info):
            continue

        # Check for any flags that must be set.
        has_flags = match_info.get('has_flags', {})

        if has_flags:
            flags_match = True

            for flag_name, flag_value in has_flags.items():
                if ((flag_value and flag_name not in flags) or
                    (not flag_value and flag_name in flags)):
                    flags_match = False
                    break

            if not flags_match:
                continue

        # This is a match. Add any packages.
        setup_commands += candidate.get('commands', [])

        added_packages = candidate.get('packages', [])
        skipped_packages = candidate.get('skip_packages', [])
        allow_fail = candidate.get('allow_fail', False)
        set_flags = candidate.get('set_flags', {})

        if allow_fail:
            block_i = i
        else:
            block_i = -1

        key = (install_method, block_i)
        packages_for_type = packages.setdefault(key, [])
        packages_set_for_type = packages_set.setdefault(key, set())
        allow_fail_map[key] = allow_fail

        for flag_name, flag_value in set_flags.items():
            if flag_value:
                flags.add(flag_name)
            else:
                flags.discard(flag_name)

        if added_packages:
            # We have packages to add to the final list.
            packages_for_type += added_packages
            packages_set_for_type.update(added_packages)

        if skipped_packages:
            # We have packages to skip from the final list. These are ones
            # that were added in a previous candidate but no longer apply in
            # a more specific one.
            for package in skipped_packages:
                if package in packages_set_for_type:
                    packages_for_type.remove(package)
                    packages_set_for_type.remove(package)

    install_steps: InstallSteps = [
        {
            'install_method': InstallMethodType.SHELL,
            'name': 'Setting up support for packages',
            'state': setup_command,
        }
        for setup_command in setup_commands
    ]

    for key, method_packages in packages.items():
        install_method = key[0]

        install_steps.append({
            'allow_fail': allow_fail_map[key],
            'install_method': install_method,
            'name': description or _('Installing packages'),
            'state': method_packages,
        })

    return install_steps


def get_setup_virtualenv_steps(
    install_state: InstallState,
) -> InstallSteps:
    """Return steps for setting up a virtual environment.

    Version Added:
        1.0

    Args
        install_state (rbinstall.state.InstallState):
            The state for the installation.

    Returns:
        list of _InstallStep:
        The resulting list of steps.
    """
    system_info = install_state['system_info']
    bootstrap_python_exe = system_info['bootstrap_python_exe']
    system_python_exe = system_info['system_python_exe']

    return [
        {
            'install_method': InstallMethodType.SHELL,
            'name': _('Creating Python virtual environment'),
            'state': [
                bootstrap_python_exe,
                '-m',
                'virtualenv',
                '--download',
                '-p',
                system_python_exe,
                install_state['venv_path'],
            ],
        },
    ]


def get_install_rb_packages_steps(
    install_state: InstallState,
) -> InstallSteps:
    """Return steps for setting up Review Board packages.

    Version Added:
        1.0

    Args
        install_state (rbinstall.state.InstallState):
            The state for the installation.

    Returns:
        list of _InstallStep:
        The resulting list of steps.
    """
    packages: List[str] = []

    for package_name, version_key in (('ReviewBoard',
                                       'reviewboard_version_info'),
                                      ('ReviewBoardPowerPack',
                                       'powerpack_version_info'),
                                      ('reviewbot-extension',
                                       'reviewbot_extension_version_info'),
                                      ('reviewbot-worker',
                                       'reviewbot_worker_version_info')):
        version_info = install_state[version_key]  # type: ignore

        if version_info:
            version = version_info['version']
            packages.append(f'{package_name}=={version}')

    return [
        {
            'install_method': InstallMethodType.PIP,
            'name': _('Installing Review Board packages'),
            'state': packages,
        }
    ]


def get_install_steps(
    *,
    install_state: InstallState,
) -> InstallSteps:
    """Return all steps for installing Review Board.

    Version Added:
        1.0

    Args
        install_state (rbinstall.state.InstallState):
            The state for the installation.

    Returns:
        list of _InstallStep:
        The resulting list of steps.
    """
    categories: List[str] = [
        'common',
        'cvs',
        'django-storages',
        'git',
        'memcached',
        'mercurial',
        'mysql',
        'perforce',
        'postgres',
        'subversion',
        'saml',
    ]

    return [
        *get_install_package_steps(
            install_state,
            categories=categories,
            description=_('Installing system packages'),
            package_type='system'),
        *get_setup_virtualenv_steps(install_state),
        *get_install_package_steps(
            install_state,
            categories=categories,
            description=_('Installing Python packaging support'),
            package_type='virtualenv'),
        *get_install_rb_packages_steps(install_state),
        *get_install_package_steps(
            install_state,
            categories=categories,
            description=_('Installing extra Review Board integrations'),
            package_type='rb-extras'),
        *get_install_package_steps(
            install_state,
            categories=categories,
            description=_('Installing service integrations'),
            package_type='service-integrations'),
    ]
