"""Utilities for working with processes and output.

Version Added:
    1.0
"""

# NOTE: This file must be syntactically compatible with Python 3.7+.
from __future__ import annotations

import os
import subprocess
import shlex
import sys
from typing import List, Mapping, NoReturn, Optional, Sequence

from rich.markup import escape as rich_escape
from typing_extensions import NotRequired, TypedDict

from rbinstall.errors import RunCommandError
from rbinstall.ui import get_console


DEBUG = (os.environ.get('RBINSTALL_DEBUG') == '1')


class RunKwargs(TypedDict):
    """Keyword arguments supported by the :py:func:`run` method.

    See :py:func:`run` for documentation on these arguments.

    Version Added:
        1.0
    """

    capture_command: NotRequired[Optional[List[List[str]]]]
    displayed_command: NotRequired[Optional[List[str]]]
    dry_run: NotRequired[bool]
    raw: NotRequired[bool]


def die(
    msg: str,
) -> NoReturn:
    """Print an error and exit.

    Version Added:
        1.0

    Args:
        msg (str):
            The message to display.
    """
    sys.stderr.write(f'{msg}\n')
    sys.exit(1)


def debug(
    msg: str,
    *,
    show_prefix: bool = True,
) -> None:
    """Output debug information.

    This will only be shown if the :envvar:`RBINSTALL_DEBUG` environment
    variable is set to ``1``.

    Version Added:
        1.0

    Args:
        msg (str, optional):
            The message to display.
    """
    if DEBUG:
        if show_prefix:
            print(f'[DEBUG] {msg}')
        else:
            print(msg)


def run(
    command: List[str],
    *,
    capture_command: Optional[List[List[str]]] = None,
    displayed_command: Optional[List[str]] = None,
    dry_run: bool = False,
    raw: bool = False,
    env: Mapping[str, str] = None,
) -> None:
    """Run an external command.

    Output will be streamed.

    Version Added:
        1.0

    Args:
        command (list of str):
            The full command line to run.

        capture_command (list of list of str, optional):
            If provided as a list, the command to run will be stored in the
            list.

        displayed_command (list of str, optional):
            An optional command to show for display purposes, instead of the
            actual command.

        dry_run (bool, optional):
            Whether to perform a dry-run of the command.

            If ``True``, the command won't be executed.

        raw (bool, optional):
            Whether to execute with raw output to the terminal.

        env (dict, optional):
            Extra environment variables for the process.

    Raises:
        rbinstall.errors.RunCommandError:
            There was an error running the command.
    """
    console = get_console()

    if not displayed_command:
        displayed_command = command

    if capture_command is None:
        displayed_command_str = rich_escape(join_cmdline(displayed_command))
        console.print(
            f'[command.prompt]$[/] [command.line]{displayed_command_str}[/]',
            highlight=False)
    else:
        capture_command.append(displayed_command)

    if env:
        env = dict(os.environ, **env)
    else:
        env = os.environ

    if not dry_run:
        if raw:
            try:
                subprocess.run(command,
                               check=True,
                               env=env)
            except subprocess.CalledProcessError as e:
                raise RunCommandError(command=command,
                                      exit_code=e.returncode)
        else:
            with subprocess.Popen(command,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT,
                                  env=env) as p:
                assert p.stdout is not None

                while p.poll() is None:
                    console.out(p.stdout.read1().decode('utf-8', 'ignore'),
                                style='dim',
                                highlight=False,
                                end='')

                # Write anything remaining in the buffer.
                console.out(p.stdout.read().decode('utf-8', 'ignore'),
                            style='dim',
                            highlight=False,
                            end='')

                exit_code = p.poll()

                debug(f'exit code = {exit_code}')

                if exit_code != 0:
                    assert exit_code is not None
                    raise RunCommandError(command=command,
                                          exit_code=exit_code)


def join_cmdline(
    cmdline: Sequence[str],
) -> str:
    """Return a string representation of a command line, joined from parts.

    This is similar to :py:meth:`shlex.join`, but avoids quoting characters
    such as ``|`` that might need to be represented as-is in command line
    output.

    Version Added:
        1.0

    Args:
        cmdline (list of str):
            The command line to join.

    Returns:
        str:
        The resulting command line string.
    """
    parts: List[str] = []

    for part in cmdline:
        if part != '|':
            part = shlex.quote(part)

        parts.append(part)

    return ' '.join(parts)
