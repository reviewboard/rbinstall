"""Unit tests for rbinstall.versioning.

Version Added:
    1.0
"""

from __future__ import annotations

from unittest import TestCase

from rbinstall.versioning import parse_version


class ParseVersionTests(TestCase):
    """Unit tests for parse_version().

    Version Added:
        1.0
    """

    def test_with_ints(self) -> None:
        """Testing parse_version with all integers"""
        self.assertEqual(parse_version('1.2.3'), (1, 2, 3))

    def test_with_strings(self) -> None:
        """Testing parse_version with all strings"""
        self.assertEqual(parse_version('a.b.c'), ('a', 'b', 'c'))

    def test_with_mixed(self) -> None:
        """Testing parse_version with mixed integers and strings"""
        self.assertEqual(parse_version('1.2.abc'), (1, 2, 'abc'))
