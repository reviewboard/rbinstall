"""Unit tests for rbinstall.pypi.

Version Added:
    1.0
"""

from __future__ import annotations

import json
import re
from contextlib import contextmanager
from io import StringIO
from typing import Any, Dict, TYPE_CHECKING, Tuple
from unittest import TestCase
from urllib.error import HTTPError
from urllib.request import urlopen

import kgb

from rbinstall.errors import InstallerError
from rbinstall.install_methods import InstallMethodType
from rbinstall.pypi import get_package_version_info

if TYPE_CHECKING:
    from rbinstall.state import SystemInfo


class GetPackageVersionInfoTests(kgb.SpyAgency, TestCase):
    """Unit tests for get_package_version_info().

    Version Added:
        1.0
    """

    def test_with_latest_match(self) -> None:
        """Testing get_package_version_info with latest version match"""
        self._setup_response({
            'info': {
                'name': 'ReviewBoard',
                'version': '6.0.1',
            },
            'releases': {
                '4.0': [],
                '6.0.1': [
                    {
                        'requires_python': '>=3.8',
                    },
                ],
            },
        })

        info = get_package_version_info(
            system_info=self.create_system_info(),
            package_name='ReviewBoard',
            target_version='latest')

        self.assertEqual(
            info,
            {
                'is_latest': True,
                'is_requested': True,
                'latest_version': '6.0.1',
                'package_name': 'ReviewBoard',
                'requires_python': '>=3.8',
                'version': '6.0.1',
            })

    def test_with_specific_latest_match(self) -> None:
        """Testing get_package_version_info with specific latest version match
        """
        self._setup_response({
            'info': {
                'name': 'ReviewBoard',
                'version': '6.0.1',
            },
            'releases': {
                '4.0': [],
                '6.0.1': [
                    {
                        'requires_python': '>=3.8',
                    },
                ],
            },
        })

        info = get_package_version_info(
            system_info=self.create_system_info(),
            package_name='ReviewBoard',
            target_version='6.0.1')

        self.assertEqual(
            info,
            {
                'is_latest': True,
                'is_requested': True,
                'latest_version': '6.0.1',
                'package_name': 'ReviewBoard',
                'requires_python': '>=3.8',
                'version': '6.0.1',
            })

    def test_with_below_latest_match(self) -> None:
        """Testing get_package_version_info with below latest version match"""
        self._setup_response({
            'info': {
                'name': 'ReviewBoard',
                'version': '6.0.1',
            },
            'releases': {
                '4.0': [],
                '5.0': [
                    {
                        'requires_python': '>=3.7',
                    },
                ],
                '6.0.1': [
                    {
                        'requires_python': '>=3.8',
                    },
                ],
            },
        })

        info = get_package_version_info(
            system_info=self.create_system_info(python_version=(3, 7, 0)),
            package_name='ReviewBoard',
            target_version='latest')

        self.assertEqual(
            info,
            {
                'is_latest': False,
                'is_requested': False,
                'latest_version': '6.0.1',
                'package_name': 'ReviewBoard',
                'requires_python': '>=3.7',
                'version': '5.0',
            })

    def test_with_no_match(self) -> None:
        """Testing get_package_version_info with no match"""
        self._setup_response({
            'info': {
                'name': 'ReviewBoard',
                'version': '6.0.1',
            },
            'releases': {
                '5.0': [
                    {
                        'requires_python': '>=3.7',
                    },
                ],
                '6.0.1': [
                    {
                        'requires_python': '>=3.8',
                    },
                ],
            },
        })

        info = get_package_version_info(
            system_info=self.create_system_info(python_version=(2, 7, 0)),
            package_name='ReviewBoard',
            target_version='latest')

        self.assertIsNone(info)

    def test_with_http_error(self) -> None:
        """Testing get_package_version_info with HTTP error"""
        self.spy_on(
            urlopen,
            op=kgb.SpyOpRaise(HTTPError(
                url='https://pypi.org/pypi/ReviewBoard/json',
                code=500,
                msg='Internal Server Error',
                hdrs={},  # type: ignore
                fp=None)))

        message = re.escape(
            'Could not fetch information on the ReviewBoard packages (at '
            'https://pypi.org/pypi/ReviewBoard/json). Check your network '
            'and HTTP(S) proxy environment variables (`http_proxy` and '
            '`https_proxy`). The error was: HTTP Error 500: Internal Server '
            'Error'
        )

        with self.assertRaisesRegex(InstallerError, message):
            get_package_version_info(
                system_info=self.create_system_info(python_version=(2, 7, 0)),
                package_name='ReviewBoard',
                target_version='latest')

    def test_with_http_error_404(self) -> None:
        """Testing get_package_version_info with HTTP error 404"""
        self.spy_on(
            urlopen,
            op=kgb.SpyOpRaise(HTTPError(
                url='https://pypi.org/pypi/ReviewBoard/json',
                code=404,
                msg='Not Found',
                hdrs={},  # type: ignore
                fp=None)))

        info = get_package_version_info(
            system_info=self.create_system_info(),
            package_name='ReviewBoard',
            target_version='latest')

        self.assertIsNone(info)

    def test_with_parse_error(self) -> None:
        """Testing get_package_version_info with parse error"""
        self._setup_response({})

        message = re.escape(
            "Could not parse information on ReviewBoard packages (at "
            "https://pypi.org/pypi/ReviewBoard/json). This may indicate an "
            "issue accessing https://pypi.org/ or an issue with the requested "
            "version of Review Board. The error was: 'info'"
        )

        with self.assertRaisesRegex(InstallerError, message):
            get_package_version_info(
                system_info=self.create_system_info(),
                package_name='ReviewBoard',
                target_version='latest')

    def create_system_info(
        self,
        *,
        python_version: Tuple[int, int, int] = (3, 11, 0),
    ) -> SystemInfo:
        """Return sample system information for testing.

        Args:
            python_version (tuple of int):
                A 3-tuple for the Python version to test with.

        Returns:
            rbinstall.state.SystemInfo:
            The generated system information.
        """
        return {
            'arch': 'amd64',
            'bootstrap_python_exe': '/path/to/bootstrap/python',
            'paths': {},
            'system_install_method': InstallMethodType.APT,
            'system': 'Linux',
            'system_python_exe': '/usr/bin/python',
            'system_python_version': (*python_version, '', 0),
            'version': '1.2.3',
        }

    def _setup_response(
        self,
        rsp: Dict[str, Any],
    ) -> None:
        """Set up an HTTP response for a test.

        Args:
            rsp (dict):
                The payload to return in the response.
        """
        @self.spy_for(urlopen)
        @contextmanager
        def _urlopen(request, *args, **kwargs):
            headers = request.headers

            self.assertEqual(request.get_full_url(),
                             'https://pypi.org/pypi/ReviewBoard/json')
            self.assertEqual(headers['Accept'], 'application/json')
            self.assertTrue(headers['User-agent'].startswith('rbinstall/'))

            yield StringIO(json.dumps(rsp))
