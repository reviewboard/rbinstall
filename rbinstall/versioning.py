"""Utilities for working with version information.

Version Added:
    1.0
"""

# NOTE: This file must be syntactically compatible with Python 3.7+.
from __future__ import annotations

import operator
from functools import partialmethod
from typing import Any, Callable, List, Tuple, TypeVar, Union

from typing_extensions import TypeAlias


_ParsedVersionPart: TypeAlias = Union[int, str]
_ParsedVersionPartT = TypeVar('_ParsedVersionPartT', int, str)


class _ComparedVersionPart:
    """A wrapper for version parts, to aid in comparison.

    This will compare integers to integers, and otherwise compare two values
    as strings.

    Version Added:
        1.0
    """

    ######################
    # Instance variables #
    ######################

    part: _ParsedVersionPart

    def __init__(
        self,
        part: _ParsedVersionPart,
    ) -> None:
        """Initialize the wrapper.

        Args:
            part (int or str):
                The version part for comparison.
        """
        self.part = part

    def _compare(
        self,
        other: object,
        *,
        op: Callable[[Any, Any], bool],
    ) -> bool:
        """Compare the wrapped value with another.

        If both are integers, they will be compared as-is with the given
        operator. Otherwise, they'll first be normalized to strings and then
        compared.

        Args:
            other (object):
                The other object for comparison.

            op (callable):
                The operator used to compare the values.

        Returns:
            bool:
            The results of the operator on the normalized values.
        """
        if not isinstance(other, _ComparedVersionPart):
            return False

        a = self.part
        b = other.part
        is_a_int = isinstance(a, int)
        is_b_int = isinstance(b, int)

        if is_a_int != is_b_int:
            a = str(a)
            b = str(b)

        return op(a, b)

    __ge__ = partialmethod(_compare, op=operator.ge)
    __gt__ = partialmethod(_compare, op=operator.gt)
    __le__ = partialmethod(_compare, op=operator.le)
    __lt__ = partialmethod(_compare, op=operator.lt)

    # Note that we have to ignore the type on operator.eq, because instead
    # of checking for comparable types, it hard-codes "object" specifically.
    __eq__ = partialmethod(_compare, op=operator.eq)  # type: ignore


def parse_version(
    version: str,
) -> ParsedVersion:
    """Return a tuple representing a parsed version string.

    The string is expected to be ``.``-delimited. It will be converted to
    a tuple, with any numbers converted to integers.

    Version Added:
        1.0

    Args:
        version (str):
            The version to parse.

    Returns:
        tuple:
        The parsed version tuple.
    """
    part: _ParsedVersionPart

    info: List[_ParsedVersionPart] = []

    for part in version.split('.'):
        try:
            part = int(part)
        except ValueError:
            pass

        info.append(part)

    return tuple(info)


def match_version(
    *matched_version_info: _ParsedVersionPart,
    op: Callable[[Tuple[_ComparedVersionPart, ...],
                  Tuple[_ComparedVersionPart, ...]], bool] = operator.eq,
) -> VersionMatchFunc:
    """Match a computed version to an expected version.

    This will check for equality by default, but can take an operator to
    perform other comparisons.

    Version Added:
        1.0

    Args:
        *matched_version_info (tuple of int):
            The version parts to compare against.

        op (callable, optional):
            The operator used for comparison.

    Returns:
        callable:
        The version comparator.
    """
    def _match(
        version_info: Tuple[_ParsedVersionPart, ...],
    ) -> bool:
        return op(
            tuple(
                _ComparedVersionPart(part)
                for part in version_info
            ),
            tuple(
                _ComparedVersionPart(part)
                for part in matched_version_info
            ))

    return _match


#: A parsed version tuple.
#:
#: This may consist of both integers and strings.
#:
#: Version Added:
#:     1.0
ParsedVersion: TypeAlias = Tuple[_ParsedVersionPart, ...]


#: A function that can match a version.
#:
#: Version Added:
#:     1.0
VersionMatchFunc: TypeAlias = Callable[[Tuple[_ParsedVersionPart, ...]],
                                       bool]
