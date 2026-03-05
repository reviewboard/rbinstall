"""Unit tests for rbinstall.versioning.

Version Added:
    1.0
"""

from __future__ import annotations

from unittest import TestCase

from rbinstall.versioning import NO_VERSION, match_version, parse_version


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

    def test_with_empty_string(self) -> None:
        """Testing parse_version with an empty string"""
        self.assertEqual(parse_version(''), ())


class MatchVersionTests(TestCase):
    """Unit tests for match_version().

    Version Added:
        1.3
    """

    def test_with_no_version_and_empty_version(self) -> None:
        """Testing match_version(NO_VERSION) with an empty version tuple"""
        self.assertTrue(match_version(NO_VERSION)(()))

    def test_with_no_version_and_versioned(self) -> None:
        """Testing match_version(NO_VERSION) with a versioned distro"""
        self.assertFalse(match_version(NO_VERSION)((10,)))

    def test_with_version_and_empty_version(self) -> None:
        """Testing match_version with a version against an empty tuple"""
        self.assertFalse(match_version(10)(()))
