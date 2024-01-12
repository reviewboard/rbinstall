"""Errors for the installation process.

Version Added:
    1.0
"""

# NOTE: This file must be syntactically compatible with Python 3.7+.
from __future__ import annotations

from typing import List


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
