"""System and installation state.

Version Added:
    1.0
"""

# NOTE: This file must be syntactically compatible with Python 3.7+.
from __future__ import annotations

import os
import platform
import re
import subprocess
import sys
import sysconfig
from typing import Dict, List, Optional, Set, TYPE_CHECKING, Tuple

from typing_extensions import NotRequired, TypedDict

from rbinstall.errors import InstallerError
from rbinstall.install_methods import InstallMethodType
from rbinstall.process import debug

if TYPE_CHECKING:
    from rbinstall.install_steps import InstallSteps
    from rbinstall.pypi import PackageVersionInfo


DOCS_URL = 'https://www.reviewboard.org/docs/manual/latest/'
INSTALLATION_DOCS_URL = f'{DOCS_URL}admin/installation/'


class SystemInfo(TypedDict):
    """Information on the current system.

    Version Added:
        1.0
    """

    #: The architecture of the system.
    arch: str

    #: The path to the bootstrap Python.
    bootstrap_python_exe: str

    #: A mapping of names to paths.
    #:
    #: This is system-dependent.
    paths: Dict[str, str]

    #: The primary install method for system packages.
    system_install_method: InstallMethodType

    #: The name of the system.
    #:
    #: Supported systems are "Darwin" and "Linux".
    system: str

    #: The path to the system Python.
    system_python_exe: str

    #: The version of the system Python.
    #:
    #: This may be the Python within rbinstall's bootstrapped virtualenv.
    system_python_version: Tuple[int, int, int, str, int]

    #: The version of the operating system or distribution.
    version: str

    #: The list of compatible Linux distribution families.
    #:
    #: This is only set if :py:attr:`system` is "Linux".
    distro_families: NotRequired[Optional[Set[str]]]

    #: The full name of the Linux distribution.
    #:
    #: This is only set if :py:attr:`system` is "Linux".
    distro_full_name: NotRequired[Optional[str]]

    #: The ID of the Linux distribution.
    #:
    #: This is only set if :py:attr:`system` is "Linux".
    distro_id: NotRequired[Optional[str]]

    #: The short name of the Linux distribution.
    #:
    #: This is only set if :py:attr:`system` is "Linux".
    distro_name: NotRequired[Optional[str]]


class InstallState(TypedDict):
    """The state chosen and computed for installation.

    Version Added:
        1.0
    """

    #: Whether to create a site directory.
    create_sitedir: bool

    #: Whether to perform a dry-run of the installation.
    dry_run: bool

    #: Whether the Review Bot extension will be installed.
    install_reviewbot_extension: bool

    #: Whether the Review Bot worker will be installed.
    install_reviewbot_worker: bool

    #: Whether Power Pack will be installed.
    install_powerpack: bool

    #: The version of Power Pack to install.
    powerpack_version_info: Optional[PackageVersionInfo]

    #: The version of Review Board that will be installed.
    reviewboard_version_info: PackageVersionInfo

    #: The version of the Review Bot extension to install.
    reviewbot_extension_version_info: Optional[PackageVersionInfo]

    #: The version of the Review Bot worker to install.
    reviewbot_worker_version_info: Optional[PackageVersionInfo]

    #: The path to a site directory to create.
    sitedir_path: str

    #: The installation steps to perform.
    steps: InstallSteps

    #: The information calculated for the system.
    system_info: SystemInfo

    #: Whether this is an unattended install.
    #:
    #: Unattended installs don't prompt for input and accept all reasonable
    #: defaults.
    unattended_install: bool

    #: The path to the destination virtual environment.
    venv_path: str

    #: The path to :command:`pip` in the destination virtual environment.
    venv_pip_exe: str

    #: The path to :command:`python` in the destination virtual environment.
    venv_python_exe: str


def get_system_info() -> SystemInfo:
    """Return information on the current system.

    This will use information based on the system and architecture determined
    by Python, and will scan relevant files on the system to gather additional
    information.

    The following environment variables can be used to override some of the
    output:

    :envvar:`RBINSTALL_FORCE_SYSTEM`:
        The system to force ("Darwin" or "Linux").

    :envvar:`RBINSTALL_FORCE_ARCH`:
        The computed architecture ("aarch64" or "x86_64").

    :envvar:`RBINSTALL_OS_RELEASE_FILE`:
        The path to the :file:`os-release` file for the system, when the
        system is "Linux".

    Version Added:
        1.0

    Returns:
        SystemInfo:
        The computed information on the system.

    Raises:
        rbinstall.errors.InstallerError:
            There was an error computing system information.
    """
    debug('Fetching information on the current system...')

    system_info: SystemInfo
    system_install_method: Optional[InstallMethodType]

    system = os.environ.get('RBINSTALL_FORCE_SYSTEM') or platform.system()
    arch = os.environ.get('RBINSTALL_FORCE_ARCH') or platform.machine()

    paths: Dict[str, str] = {}

    bootstrap_python_exe = sys.executable
    system_python_exe = (
        os.environ.get('RBINSTALL_FORCE_SYSTEM_PYTHON_EXE') or
        getattr(sys, '_base_executable', None) or
        os.path.join(sysconfig.get_config_var('BINDIR'), 'python')
    )
    system_python_version: Tuple[int, int, int, str, int] = \
        tuple(sys.version_info)  # type: ignore

    if system == 'Linux':
        # This is a Linux system.
        #
        # We'll be looking for a "os-release" file, which will tell us
        # information about the Linux distribution. From that, we can
        # determine the default method for installation, and what packages
        # we need to install.
        debug('Found Linux. Fetching distribution information...')

        distro_info = get_linux_distro_info()

        if not distro_info:
            raise InstallerError(
                f'Could not determine the distribution of Linux being used. '
                f'This indicates you may be missing /etc/os-release and '
                f'/usr/lib/os-release files. You may need to install through '
                f'another method. See {INSTALLATION_DOCS_URL} for '
                f'instructions.'
            )

        debug(f'Distribution information = {distro_info!r}')

        # Determine the Linux distro families supported by this distro.
        distro_id = distro_info.get('ID')
        id_like = distro_info.get('ID_LIKE')
        families: Set[str] = set()

        if distro_id:
            families.add(distro_id)

        if id_like:
            families.update(id_like.split())

        families_str = ', '.join(sorted(families))

        debug(f'Linux families = {families_str}')

        # Determine the install methods enabled for this distro.
        debug('Determining the default install method...')
        system_install_method = get_default_linux_install_method(
            families=families)
        debug(f'Install method = {system_install_method!r}')

        if not system_install_method:
            raise InstallerError(
                f"The Review Board installer doesn't support installing on "
                f"this family of Linux ({families_str}). Please contact "
                f"support@beanbaginc.com for assistance. You may need to "
                f"install through another method. See "
                f"{INSTALLATION_DOCS_URL} for instructions."
            )

        distro_name = distro_info.get('NAME')

        # Build the system information.
        system_info = {
            'arch': arch,
            'bootstrap_python_exe': bootstrap_python_exe,
            'distro_families': families,
            'distro_full_name': distro_info.get('PRETTY_NAME') or distro_name,
            'distro_id': distro_id,
            'distro_name': distro_name,
            'paths': paths,
            'system': system,
            'system_install_method': system_install_method,
            'system_python_exe': system_python_exe,
            'system_python_version': system_python_version,
            'version': distro_info.get('VERSION_ID') or '',
        }
    elif system == 'Darwin':
        # This is a macOS system.
        #
        # On macOS, we can use brew to install dependencies.
        debug('Found macOS. Please note, Brew is required.')

        mac_ver = platform.mac_ver()

        if not mac_ver[0]:
            raise InstallerError(
                f'Python reports that this is macOS, but no macOS version was '
                f'found! This seems to be a Python installation issue. You '
                f'may need to install through another method. See '
                f'{INSTALLATION_DOCS_URL} for instructions.'
            )

        # Determine if brew is available.
        try:
            brew_prefix = (
                subprocess.check_output(['brew', '--prefix'])
                .strip()
                .decode('utf-8')
            )
            system_install_method = InstallMethodType.BREW

            debug(f'Brew is available at {brew_prefix}')
            paths['brew'] = brew_prefix
        except (FileNotFoundError, subprocess.CalledProcessError):
            debug('Brew is not installed.')

            raise InstallerError(
                f"The Review Board installer cannot install on macOS without "
                f"Brew (https://brew.sh). You may need to install through "
                f"another method. See {INSTALLATION_DOCS_URL} for "
                f"instructions."
            )

        system_info = {
            'arch': arch,
            'bootstrap_python_exe': bootstrap_python_exe,
            'paths': paths,
            'system': system,
            'system_install_method': system_install_method,
            'system_python_exe': system_python_exe,
            'system_python_version': system_python_version,
            'version': mac_ver[0],
        }
    else:
        # This is an incompatible system.
        raise InstallerError(
            f'Review Board can only be installed in Linux or macOS using this '
            f'installation script. You may need to install through another '
            f'method. See {INSTALLATION_DOCS_URL} for instructions.'
        )

    debug('System info: %r' % (system_info,))

    return system_info


def get_linux_distro_info() -> Dict[str, str]:
    """Return information on the Linux distribution.

    Version Added:
        1.0

    Returns:
        dict:
        The dictionary on parsed Linux distribution information.
    """
    # NOTE: Python 3.10+ includes platform.freedesktop_os_release(), but
    #       we can't pass in a custom path for that. So we'll use our own
    #       logic.
    distro_info: Dict[str, str] = {}

    # As per the freedesktop.org standard, and the Python logic for parsing
    # this, we need to handle values with optional single or double quotes,
    # and we need to manage special escaping rules.
    os_release_paths: List[str]

    line_re = re.compile(
        '^(?P<name>[a-zA-Z0-9_]+)=(?P<quote>[\"\']?)'
        '(?P<value>.*)(?P=quote)$'
    )
    unescape_re = re.compile(r'\\([\\\$\"\'`])')

    # NOTE: This is primarily for debugging and testing.
    custom_os_release_file = os.environ.get('RBINSTALL_OS_RELEASE_FILE')

    if custom_os_release_file:
        os_release_paths = [custom_os_release_file]
    else:
        os_release_paths = [
            '/etc/os-release',
            '/usr/lib/os-release',
        ]

    debug(f'Checking for an os-release file (considering '
          f'{os_release_paths!r})')

    for path in os_release_paths:
        if os.path.exists(path):
            debug(f'Parsing {path}...')

            with open(path, 'r') as fp:
                for line in fp.readlines():
                    m = line_re.match(line)

                    if m:
                        distro_info[m.group('name')] = \
                            unescape_re.sub(r'\1', m.group('value'))

            # We found a file, so bail. We don't want to read more.
            break

    return distro_info


def get_default_linux_install_method(
    *,
    families: Set[str],
) -> Optional[InstallMethodType]:
    """Return the default install method for a set of families.

    Version Added:
        1.0

    Args:
        families (set of str):
            The families for the Linux distribution.

    Returns:
        rbinstall.install_methods.InstallMethodType:
        The default install method, or ``None`` if not found.
    """
    if 'debian' in families:
        return InstallMethodType.APT
    elif 'rhel' in families or 'fedora' in families:
        return InstallMethodType.YUM
    elif 'arch' in families:
        return InstallMethodType.PACMAN
    elif 'opensuse' in families:
        return InstallMethodType.ZYPPER

    return None
