"""Installation methods for operating systems and distros.

Version Added:
    1.0
"""

# NOTE: This file must be syntactically compatible with Python 3.7+.
from __future__ import annotations

import os
import tempfile
import urllib.request
from enum import Enum
from typing import Dict, List, Set, TYPE_CHECKING, TypeVar

from rbinstall.errors import RunCommandError, InstallPackageError
from rbinstall.process import run

if TYPE_CHECKING:
    from typing_extensions import Protocol

    from rbinstall.process import RunKwargs
    from rbinstall.state import InstallState

    _T = TypeVar('_T')

    class _InstallMethod(Protocol):
        def __call__(
            self,
            install_state: InstallState,
            packages: List[str],
            *,
            run_kwargs: RunKwargs,
        ) -> None:
            ...


class InstallMethodType(str, Enum):
    """Types of installation methods on operating systems and distros.

    Version Added:
        1.0
    """

    #: The Debian/Ubuntu apt/apt-get package manager.
    APT = 'apt'

    #: The Debian/Ubuntu apt-get build-dep command.
    APT_BUILD_DEP = 'apt-build-dep'

    #: The macOS brew package manager.
    BREW = 'brew'

    #: The Arch Linux pacman package manager.
    PACMAN = 'pacman'

    #: The standard pip Python package manager.
    PIP = 'pip'

    #: Download and execution of an online Python script.
    REMOTE_PYSCRIPT = 'remote-pyscript'

    #: Extra package installation targets for Review Board.
    REVIEWBOARD_EXTRA = 'reviewboard-extra'

    #: A shell command.
    SHELL = 'shell'

    #: The RedHat/CentOS/Fedora/etc. "yum" package manager.
    YUM = 'yum'

    #: The OpenSuSE zypper package manager.
    ZYPPER = 'zypper'

    #: An indicator of the default system package tool for a target system.
    SYSTEM_DEFAULT = 'system-default'


def _run_apt_install(
    install_state: InstallState,
    packages: List[str],
    *,
    run_kwargs: RunKwargs,
) -> None:
    """Run the :command:`apt-get install` command.

    Version Added:
        1.0

    Args:
        install_state (rbinstall.state.InstallState):
            The state for the installation.

        packages (list of str):
            The list of packages to install.

    Raises:
        rbinstall.errors.InstallPackageError:
            The package failed to install.
    """
    try:
        run(['apt-get', 'install', '-y'] + packages,
            **run_kwargs)
    except RunCommandError as e:
        raise InstallPackageError(install_state=install_state,
                                  install_method=InstallMethodType.APT,
                                  packages=packages,
                                  error=e)


def _run_apt_build_dep(
    install_state: InstallState,
    packages: List[str],
    *,
    run_kwargs: RunKwargs,
) -> None:
    """Run the :command:`apt-get build-dep` command.

    Version Added:
        1.0

    Args:
        install_state (rbinstall.state.InstallState):
            The state for the installation.

        packages (list of str):
            The list of packages to install build-time dependencies for.

    Raises:
        rbinstall.errors.InstallPackageError:
            The package failed to install.
    """
    try:
        run(['apt-get', 'build-dep', '-y'] + packages,
            **run_kwargs)
    except RunCommandError as e:
        raise InstallPackageError(
            install_state=install_state,
            install_method=InstallMethodType.APT_BUILD_DEP,
            packages=packages,
            error=e)


def _run_brew_install(
    install_state: InstallState,
    packages: List[str],
    *,
    run_kwargs: RunKwargs,
) -> None:
    """Run the :command:`brew` command.

    Version Added:
        1.0

    Args:
        install_state (rbinstall.state.InstallState):
            The state for the installation.

        packages (list of str):
            The list of packages to install.

    Raises:
        rbinstall.errors.InstallPackageError:
            The package failed to install.
    """
    try:
        run(['brew', 'install'] + packages,
            **run_kwargs)
    except RunCommandError as e:
        raise InstallPackageError(install_state=install_state,
                                  install_method=InstallMethodType.BREW,
                                  packages=packages,
                                  error=e)


def _run_pacman_install(
    install_state: InstallState,
    packages: List[str],
    *,
    run_kwargs: RunKwargs,
) -> None:
    """Run the :command:`pacman -S` command.

    Version Added:
        1.0

    Args:
        install_state (rbinstall.state.InstallState):
            The state for the installation.

        packages (list of str):
            The list of packages to install.

    Raises:
        rbinstall.errors.InstallPackageError:
            The package failed to install.
    """
    try:
        run(
            [
                'pacman',
                '-S',
                '--noconfirm',
                *packages,
            ],
            **run_kwargs)
    except RunCommandError as e:
        raise InstallPackageError(install_state=install_state,
                                  install_method=InstallMethodType.PACMAN,
                                  packages=packages,
                                  error=e)


def _run_pip_install(
    install_state: InstallState,
    packages: List[str],
    extra_args: List[str] = [],
    *,
    run_kwargs: RunKwargs,
) -> None:
    """Run the :command:`pip install` command.

    This will run the version in the target virtual environment.

    Version Added:
        1.0

    Args:
        install_state (rbinstall.state.InstallState):
            The state for the installation.

        packages (list of str):
            The list of packages to install.

        extra_args (list of str, optional):
            Extra arguments to pass when running :command:`pip`.

    Raises:
        rbinstall.errors.InstallPackageError:
            The package failed to install.
    """
    try:
        run(
            [
                install_state['venv_pip_exe'],
                'install',
                *extra_args,
                *packages,
            ],
            env={
                'CFLAGS': (
                    # Avoid warnings that can come up on some systems during
                    # compilation, depending on Python and system library
                    # versions.
                    #
                    # This was first needed for lxml on Fedora 40+, and
                    # mirrors Fedora's own RPM spec.
                    # (https://bugs.launchpad.net/lxml/+bug/2051243)
                    #
                    # We apply it everywhere as a precaution.
                    '-Wno-error=incompatible-pointer-types'
                ),
            },
            **run_kwargs)
    except RunCommandError as e:
        raise InstallPackageError(install_state=install_state,
                                  install_method=InstallMethodType.PIP,
                                  packages=packages,
                                  error=e)


def _run_remote_pyscript(
    install_state: InstallState,
    packages: List[str],
    *,
    run_kwargs: RunKwargs,
) -> None:
    """Download and run a remote Python script.

    This will download the Python script to a temp file and run it.

    Version Added:
        1.0

    Args:
        install_state (rbinstall.state.InstallState):
            The state for the installation.

        packages (list of str):
            The list of Python scripts to download and run.

            This may only contain a single entry.

    Raises:
        rbinstall.errors.InstallPackageError:
            The package failed to install.
    """
    assert len(packages) == 1

    python_exe = install_state['venv_python_exe']
    script_url = packages[0]

    displayed_command = ['curl', script_url, '|', python_exe]

    if run_kwargs.get('dry_run'):
        run(displayed_command, **run_kwargs)
    else:
        fd, script_file = tempfile.mkstemp(suffix='.py')

        try:
            with urllib.request.urlopen(script_url) as fp:
                os.write(fd, fp.read())

            os.close(fd)

            try:
                run([python_exe, script_file],
                    displayed_command=displayed_command,
                    **run_kwargs)
            except RunCommandError as e:
                raise InstallPackageError(
                    install_state=install_state,
                    install_method=InstallMethodType.REMOTE_PYSCRIPT,
                    packages=packages,
                    error=e)
        finally:
            os.unlink(script_file)


def _run_reviewboard_extra(
    install_state: InstallState,
    packages: List[str],
    *,
    run_kwargs: RunKwargs,
) -> None:
    """Install a Review Board extras package.

    Version Added:
        1.0

    Args:
        install_state (rbinstall.state.InstallState):
            The state for the installation.

        packages (list of str):
            The list of Review Board extra package names.

    Raises:
        rbinstall.errors.InstallPackageError:
            The package failed to install.
    """
    try:
        _run_pip_install(
            install_state,
            [
                f'ReviewBoard[{extra}]'
                for extra in packages
            ],
            run_kwargs=run_kwargs)
    except InstallPackageError as e:
        e.install_method = InstallMethodType.REVIEWBOARD_EXTRA
        raise


def _run_shell(
    install_state: InstallState,
    packages: List[str],
    *,
    run_kwargs: RunKwargs,
) -> None:
    """Run a shell command to install a package.

    Version Added:
        1.0

    Args:
        install_state (rbinstall.state.InstallState):
            The state for the installation.

        packages (list of str):
            The full list of command line arguments.

    Raises:
        rbinstall.errors.InstallPackageError:
            The package failed to install.
    """
    try:
        run(packages, **run_kwargs)
    except RunCommandError as e:
        raise InstallPackageError(
            install_state=install_state,
            install_method=InstallMethodType.SHELL,
            error=e,
            msg=(
                'There was an error executing the command `%(command)s`. '
                'The error was: %(detail)s'
            ))


def _run_yum_install(
    install_state: InstallState,
    packages: List[str],
    *,
    run_kwargs: RunKwargs,
) -> None:
    """Run the :command:`yum` command.

    Version Added:
        1.0

    Args:
        install_state (rbinstall.state.InstallState):
            The state for the installation.

        packages (list of str):
            The list of packages to install.

    Raises:
        rbinstall.errors.InstallPackageError:
            The package failed to install.
    """
    try:
        run(['yum', 'install', '-y'] + packages,
            **run_kwargs)
    except RunCommandError as e:
        raise InstallPackageError(install_state=install_state,
                                  install_method=InstallMethodType.YUM,
                                  packages=packages,
                                  error=e)


def _run_zypper_install(
    install_state: InstallState,
    packages: List[str],
    *,
    run_kwargs: RunKwargs,
) -> None:
    """Run the :command:`zypper install` command.

    Version Added:
        1.0

    Args:
        install_state (rbinstall.state.InstallState):
            The state for the installation.

        packages (list of str):
            The list of packages to install.

    Raises:
        rbinstall.errors.InstallPackageError:
            The package failed to install.
    """
    try:
        run(
            [
                'zypper',
                'install',
                '-y',
                *packages,
            ],
            **run_kwargs)
    except RunCommandError as e:
        raise InstallPackageError(install_state=install_state,
                                  install_method=InstallMethodType.ZYPPER,
                                  packages=packages,
                                  error=e)


def run_install_method(
    *,
    install_method: InstallMethodType,
    install_state: InstallState,
    args: List[str],
    run_kwargs: RunKwargs = {},
) -> None:
    """Run an install method with the provided arguments.

    Version Added:
        1.0

    Args:
        install_method (InstallMethodType):
            The install method type to run.

        install_state (rbinstall.state.InstallState):
            The install state for process execution.

        *args (tuple):
            The arguments to pass.

    Raises:
        rbinstall.errors.InstallPackageError:
            There was an error installing the package.
    """
    if install_state['dry_run']:
        run_kwargs['dry_run'] = True

    # Allow errors to bubble up.
    return INSTALL_METHODS[install_method](install_state, args,
                                           run_kwargs=run_kwargs)


#: A mapping of all install methods to handlers.
#:
#: Version Added:
#:     1.0
INSTALL_METHODS: Dict[str, _InstallMethod] = {
    InstallMethodType.APT: _run_apt_install,
    InstallMethodType.APT_BUILD_DEP: _run_apt_build_dep,
    InstallMethodType.BREW: _run_brew_install,
    InstallMethodType.PACMAN: _run_pacman_install,
    InstallMethodType.PIP: _run_pip_install,
    InstallMethodType.REMOTE_PYSCRIPT: _run_remote_pyscript,
    InstallMethodType.REVIEWBOARD_EXTRA: _run_reviewboard_extra,
    InstallMethodType.SHELL: _run_shell,
    InstallMethodType.YUM: _run_yum_install,
    InstallMethodType.ZYPPER: _run_zypper_install,
}


#: All the installer methods available on every target system.
#:
#: Version Added:
#:     1.0
COMMON_INSTALL_METHODS: Set[InstallMethodType] = {
    InstallMethodType.PIP,
    InstallMethodType.REMOTE_PYSCRIPT,
    InstallMethodType.REVIEWBOARD_EXTRA,
    InstallMethodType.SHELL,
}
