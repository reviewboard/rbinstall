"""Errors for the installation process.

Version Added:
    1.0
"""

# NOTE: This file must be syntactically compatible with Python 3.7+.
from __future__ import annotations

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from rbinstall.install_methods import InstallMethodType
    from rbinstall.state import InstallState


class InstallerError(Exception):
    """A common error for the installation process.

    Version Added:
        1.0
    """


class RunCommandError(InstallerError):
    """An error with running a command.

    Version Added:
        1.0
    """

    ######################
    # Instance variables #
    ######################

    #: The full command line that was executed.
    command: List[str]

    #: The exit code of the process.
    exit_code: int

    def __init__(
        self,
        *,
        command: List[str],
        exit_code: int,
    ) -> None:
        """Initialize the error.

        Args:
            command (list of str):
                The full command line that was executed.

            exit_code (int):
                The exit code of the process.
        """
        self.command = command
        self.exit_code = exit_code

        command_str = ' '.join(command)

        super().__init__(
            f'Error executing `{command_str}`: exit code {exit_code}'
        )


class InstallPackageError(InstallerError):
    """An error installing a package.

    Version Added:
        1.0
    """

    def __init__(
        self,
        *,
        error: RunCommandError,
        install_state: InstallState,
        install_method: InstallMethodType,
        packages: List[str] = [],
        msg: str = '',
    ) -> None:
        """Initialize the error.

        Args:
            error (RunCommandError):
                The command error that triggered this error.

            install_state (rbinstall.state.InstallState):
                The state for the installation.

            install_method (rbinstall.install_methods.InstallMethodType):
                The installation method that failed.

            packages (list of str, optional):
                The packages that were being installed.

            msg (str, optional):
                A custom message to return.

                This may contain ``%(package)s``, ``%(command)s``, and
                ``%(detail)s`` format strings.
        """
        self.install_method = install_method
        self.install_state = install_state
        self.packages = packages

        super().__init__(
            (msg or (
                'There was an error installing one or more packages '
                '(%(packages)s). The command that failed was: `%(command)s`. '
                'The error was: %(detail)s'
            )) % {
                'command': ' '.join(error.command),
                'detail': str(error),
                'packages': ' '.join(packages),
            }
        )
