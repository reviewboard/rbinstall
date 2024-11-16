"""UI support for the installer.

Version Added:
    1.0
"""

# NOTE: This file must be syntactically compatible with Python 3.7+.
from __future__ import annotations

import fcntl
import os
import re
import sys
import time
from gettext import gettext as _
from select import select
from typing import Any, Optional, Sequence, TYPE_CHECKING, Tuple, Union

from rich import (get_console,
                  reconfigure as reconfigure_console)
from rich.console import Console, Group
from rich.markup import escape
from rich.padding import Padding
from rich.progress import (BarColumn,
                           Progress,
                           SpinnerColumn,
                           TextColumn,
                           TimeElapsedColumn)
from rich.prompt import (Confirm as RichConfirm,
                         Prompt as RichPrompt)
from rich.table import Column, Table
from rich.theme import Theme

try:
    import termios
    import tty
except ImportError:
    termios = None  # type: ignore
    tty = None      # type: ignore

if TYPE_CHECKING:
    from rich.prompt import PromptBase
    from rich.text import TextType
else:
    PromptBase = object


class NonInteractivePromptMixin(PromptBase):
    """A mixin for non-interactive support for prompts.

    This enables prompts to display the prompt without requesting input,
    if the console is in non-interactive mode.

    Version Added:
        1.0
    """

    @classmethod
    def get_input(
        cls,
        console: Console,
        prompt: TextType,
        *args,
        **kwargs,
    ) -> str:
        """Display a prompt and return the inputted value.

        If in non-interactive mode, the prompt will be printed and an empty
        value returned. This will trigger the caller's default value handling.

        Args:
            console (rich.console.Console):
                The main Rich console object.

            prompt (str):
                The prompt text.

            *args (tuple):
                Additional positional arguments for the prompt.

            **kwargs (dict):
                Additional keyword arguments for the prompt.

        Returns:
            str:
            The inputted text.
        """
        if not console.is_interactive:
            console.print(prompt)
            return ''

        return super().get_input(console, prompt, *args, **kwargs)


class Confirm(NonInteractivePromptMixin, RichConfirm):
    """A confirmation prompt, supporting non-interactive mode.

    Version Added:
        1.0
    """


class Prompt(NonInteractivePromptMixin, RichPrompt):
    """A prompt, supporting non-interactive mode.

    Version Added:
        1.0
    """


class ShellCommand(Padding):
    """Wrapper for a displayed shell command.

    Version Added:
        1.0
    """

    def __init__(
        self,
        text: str,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the shell command wrapper.

        Args:
            text (str):
                The command line text to display.

            *args (tuple):
                Positional arguments for the wrapper.

            **kwargs (dict):
                Keyword arguments for the wrapper.
        """
        text = escape(text)

        super().__init__(f'[command.prompt]$[/] [command.line]{text}[/]',
                         (0, 4),
                         *args, **kwargs)


def init_console(
    *,
    allow_color: bool = True,
    allow_interactive: bool = True,
) -> None:
    """Initialize the console UI.

    This will attempt to determine if the terminal should be in dark or
    light mode, and then style the console accordingly. It will also opt
    out of interactive mode or color mode if needed.

    Version Added:
        1.0

    Args:
        allow_color (bool, optional):
            Whether color is allowed in the UI.

        allow_interactive (bool, optional):
            Whether the UI is allowed to prompt for input.
    """
    if not allow_color or is_terminal_dark():
        theme = Theme({
            'command.prompt': 'bold red',
            'command.line': 'white',
            'info': 'dim cyan',
            'note': 'yellow',
            'note.label': 'bold yellow',
            'progress.description': 'yellow',
            'progress.complete': 'green',
            'success': 'green',
            'warning': 'yellow',
            'error': 'red',
        })
    else:
        theme = Theme({
            'command.line': 'black',
            'command.prompt': 'bold red',
            'error': 'red',
            'info': 'dim cyan',
            'markdown.item.number': 'bold blue',
            'note': 'red',
            'note.label': 'bold red',
            'progress.complete': 'green',
            'prompt.choices': 'blue',
            'prompt.default': 'red',
            'repr.filename': 'bright_blue',
            'repr.number': 'blue',
            'repr.path': 'blue',
            'repr.str': 'blue',
            'rule.line': 'bold reverse green',
            'rule.text': 'black on green',
            'success': 'green',
            'warning': 'yellow',
        })

    styles = theme.styles
    styles['error'] = styles['repr.error']
    styles['item'] = styles['markdown.item.number']
    styles['link'] = styles['markdown.link']
    styles['path'] = styles['repr.filename']

    if allow_color:
        color_system = 'auto'
    else:
        color_system = None

    if allow_interactive:
        force_interactive = None
    else:
        force_interactive = False

    reconfigure_console(color_system=color_system,
                        force_interactive=force_interactive,
                        theme=theme)


def is_terminal_dark() -> bool:
    """Return whether the terminal is in dark mode.

    There is no true support for determining whether a terminal's background
    is light or dark. A dark terminal is pretty standard, and most UI libraries
    and tools (Rich included) assume the background will be dark.

    This will look for an :envvar:`COLORFGBG` environment variable to try to
    determine if it's explicitly in light mode. This is the closest thing to
    a standard variable for this use case.

    Version Added:
        1.0

    Returns:
        bool:
        ``True`` if the terminal is in dark mode. ``False`` if in light mode.
    """
    from rbinstall.process import debug

    debug('Attempting to determine terminal color configuration...')

    try:
        fg, *unused, bg = os.getenv('COLORFGBG', '').split(';')

        debug(f'Got COLOFGBG: Foreground = {fg}, Background = {bg}')

        # 0=black, 7=light-grey, 15=white.
        is_dark = fg in ('7', '15') and bg == '0'

        debug(f'Parsed COLORFGBG dark background result: {is_dark}')

        return is_dark
    except Exception:
        pass

    # Try an xterm-compatible terminal ANSI command for checking the
    # background color.
    debug('Querying terminal for background color...')
    xterm_bg_info = query_terminal('\033]11;?\a', terminator='\\')
    debug(f'Got terminal result = {xterm_bg_info!r}')

    if xterm_bg_info:
        # This actually comes in 4-digit R, G, and B values. We're only going
        # to look at the first digit of each. There's maybe a better way of
        # calculating dark vs. light mode here, but we're going with what Vim
        # itself does.
        m = re.search(
            r'11;rgb:'
            r'(?P<red>[0-9a-f]{1,4})/'
            r'(?P<green>[0-9a-f]{1,4})/'
            r'(?P<blue>[0-9a-f]{1,4})',
            xterm_bg_info)

        if m:
            r = m.group('red')
            g = m.group('green')
            b = m.group('blue')
            max_len = max(len(r), len(g), len(b))
            scale = 16 ** max_len - 1

            # Normalize these to numeric RGB color codes.
            r, g, b = (
                int(int(value.lstrip('0') or '0', 16) / scale * 255)
                for value in (r, g, b)
            )

            # Calculate a luma based on the background color.
            luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
            luma_pct = (luma / 255) * 100

            is_dark = luma_pct < 50

            debug(f'Queried dark background result: {is_dark}')

            return is_dark

    # Dark backgrounds are a reasonable default.
    debug('Falling back to assuming terminal background is dark.')

    return True


def query_terminal(
    ansi_code: str,
    *,
    terminator: str = '\a',
    max_len: int = 32,
) -> str:
    """Query the terminal using ANSI escape codes.

    This can be used to fetch useful information about the terminal, in an
    effort to better tailor the UI.

    The results are returned as-is, and must be further processed by the
    caller.

    Version Added:
        1.1

    Args:
        ansi_code (str):
            The ANSI code to write to the terminal.

        terminator (str, optional):
            The last character in the resulting string, used to indicate that
            all data has been read.

        max_len (int, optional):
            The maximum length to read before returning results.

            This is used as a safeguard in case data is coming from stdin but
            no terminator has been found.

    Returns:
        str:
        The resulting data from the terminal query.
    """
    if termios is None or tty is None or not os.isatty(sys.stdout.fileno()):
        return ''

    try:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        stdin_flags = fcntl.fcntl(fd, fcntl.F_GETFL)

        result = ''

        try:
            tty.setraw(fd)
            fcntl.fcntl(fd, fcntl.F_SETFL, stdin_flags | os.O_NONBLOCK)

            sys.stdout.write(ansi_code)
            sys.stdout.flush()

            # Give the terminal time to respond.
            time.sleep(0.01)

            while terminator not in result and len(result) < max_len:
                if sys.stdin not in select([sys.stdin], [], [], 0.5)[0]:
                    # We timed out. We're done reading.
                    break

                result += sys.stdin.read()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            fcntl.fcntl(fd, fcntl.F_SETFL, stdin_flags)
    except Exception:
        # Something went wrong, so just return an empty string.
        result = ''

    return result


def print_header(
    header: str,
    *,
    first: bool = False,
) -> None:
    """Print a header to the console.

    Version Added:
        1.0

    Args:
        header (str):
            The header text.

        first (bool, optional):
            Whether this is the first header displayed.
    """
    console = get_console()

    if not first:
        console.print()
        console.print()

    console.rule()
    console.print(Padding(header, (0, 1)),
                  style='rule.text')
    console.rule()
    console.print()


def print_note(
    paragraphs: Union[str, Sequence[str]],
) -> None:
    """Print a note admonition to the console.

    Version Added:
        1.0

    Args:
        paragraphs (str or list of str):
            The text or paragraphs of text to contain in the note body.
    """
    console = get_console()

    if isinstance(paragraphs, str):
        paragraphs = [paragraphs]

    table = Table.grid(Column(style='note.label'),
                       Column(style='note'),
                       padding=1)
    table.add_row(_('NOTE:'), '\n\n'.join(paragraphs))

    console.print()
    console.print(table)
    console.print()


def print_paragraphs(
    paragraphs: Union[Any, Sequence[Any]],
    *,
    leading_newline: bool = False,
    trailing_newline: bool = True,
    **kwargs,
) -> None:
    """Print one or more paragraphs of text or renderable content.

    Each paragraph will be separated by a blank line.

    Version Added:
        1.0

    Args:
        paragraphs (object or list of object):
            The content or list of per-paragraph content to display.

        leading_newline (bool, optional):
            Whether to display a leading newline before the first paragraph.

        trailing_newline (bool, optional):
            Whether to display a trailing newline after the last paragraph.
    """
    console = get_console()

    if not isinstance(paragraphs, (list, tuple)):
        paragraphs = [paragraphs]

    for i, paragraph in enumerate(paragraphs):
        if leading_newline or i > 0:
            console.print()

        console.print(paragraph, **kwargs)

    if trailing_newline:
        console.print()


def print_key_values(
    rows: Sequence[Tuple[str, str]],
) -> None:
    """Print a key/value table.

    Version Added:
        1.0

    Args:
        rows (list of tuple):
            The list of rows containing key/value pairs.

            Each is a 2-tuple in the form of:

            Tuple:
                0 (str):
                    The key.

                1 (str):
                    The value.
    """
    table = Table(box=None,
                  highlight=True,
                  show_header=False)
    table.add_column(justify='right',
                     style='bold')
    table.add_column(overflow='fold')

    for key, value in rows:
        table.add_row(f'{key}:', value)

    get_console().print(table)


def print_terms(
    terms: Sequence[Tuple[str, Any]],
) -> None:
    """Print a list of terms.

    Version Added:
        1.0

    Args:
        terms (list of tuple):
            The list of rows containing key/value pairs.

            Each is a 2-tuple in the form of:

            Tuple:
                0 (str):
                    The key.

                1 (object):
                    The descriptive content.
    """
    console = get_console()

    for name, description in terms:
        console.print(f'{name}:', style='bold')
        console.print(Padding(description, (0, 0, 0, 4)))
        console.print()


def print_ol(
    items: Sequence[Any],
) -> None:
    """Print an ordered list.

    Version Added:
        1.0

    Args:
        items (list of object):
            The list of items to display.
    """
    console = get_console()

    table = Table.grid(Column(justify='right',
                              style='item'),
                       Column(),
                       padding=1)

    for i, content in enumerate(items, start=1):
        if isinstance(content, list):
            content = Group(*content)

        table.add_row(f'{i}.', content)

    console.print(table)
    console.print()


def prompt_confirm(
    text: str,
    *,
    default: bool = False,
    unattended_default: Optional[bool] = None,
) -> bool:
    """Prompt for Yes/No confirmation.

    Version Added:
        1.0

    Args:
        text (str):
            The text to display in the prompt.

        default (bool, optional):
            The default, if Enter is pressed or if in an unattended install.

        unattended_default (bool, optional):
            An explicit default for an unattended install.

            If this is set, it will take precedence over ``default``.
    """
    if not get_console().is_interactive and unattended_default is not None:
        default = unattended_default

    return Confirm.ask(text, default=default)


def prompt_string(
    text: str,
    *,
    default: Optional[str] = None,
    unattended_default: Optional[str] = None,
) -> Optional[str]:
    """Prompt for a value.

    Version Added:
        1.0

    Args:
        text (str):
            The text to display in the prompt.

        default (bool, optional):
            The default, if Enter is pressed or if in an unattended install.

        unattended_default (bool, optional):
            An explicit default for an unattended install.

            If this is set, it will take precedence over ``default``.
    """
    if not get_console().is_interactive and unattended_default is not None:
        default = unattended_default

    return Prompt.ask(text, default=default)


def show_progress() -> Progress:
    """Show progress information for tasks.

    This shows a spinner, a text label, a progress bar, and a time-elapsed
    value.

    Version Added:
        1.0

    Returns:
        rich.progress.Progress:
        The progress manager.
    """
    return Progress(
        SpinnerColumn(finished_text='✅'),
        TextColumn('[progress.description]{task.description}'),
        BarColumn(bar_width=None),
        TimeElapsedColumn(),
        expand=True,
    )
