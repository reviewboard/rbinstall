"""PyPI lookup support.

Version Added:
    1.0
"""

from __future__ import annotations

import json
from typing import Optional, TYPE_CHECKING
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from packaging.specifiers import SpecifierSet
from packaging.version import parse as parse_version
from typing_extensions import TypedDict

from rbinstall import get_package_version
from rbinstall.errors import InstallerError
from rbinstall.process import debug

if TYPE_CHECKING:
    from rbinstall.state import SystemInfo


USER_AGENT = f'rbinstall/{get_package_version()}'


class PackageVersionInfo(TypedDict):
    """Information on a Python package to install.

    Version Added:
        1.0
    """

    #: Whether this is the latest stable version of the package.
    is_latest: bool

    #: Whether this is the requested version of the package.
    #:
    #: This will be False if an older version had to be returned for
    #: compatibility purposes.
    is_requested: bool

    #: The latest version of the package.
    latest_version: str

    #: The name of the package to install.
    package_name: str

    #: The required Python version specifier.
    requires_python: str

    #: The version of the package.
    version: str


def get_package_version_info(
    *,
    system_info: SystemInfo,
    package_name: str,
    target_version: str = 'latest',
    pypi_url: str = 'https://pypi.org',
) -> Optional[PackageVersionInfo]:
    """Return information on a version of a package.

    This will return some basic information that can be used to verify that
    the version of Review Board is available and can be installed on the
    target system.

    Args:
        system_info (rbinstall.state.SystemInfo):
            Information on the target system.

        package_name (str):
            The name of the package.

        target_version (str, optional):
            The target version of Review Board requested.

            An older version may be returned, if the target version is not
            compatible with the current system.

        pypi_url (str, optional):
            The optional URL to the PyPI server.

    Returns:
        PackageVersionInfo:
        Information on the nearest compatible version of Review Board.
    """
    url = urljoin(pypi_url, f'pypi/{package_name}/json')

    request = Request(url)
    request.add_header('Accept', 'application/json')
    request.add_header('User-Agent', USER_AGENT)

    debug(f'Fetching package information for "{package_name}" from {url}...')

    try:
        try:
            with urlopen(request) as fp:
                rsp = json.load(fp)
        except HTTPError as e:
            error_data = e.read()
            debug(f'Received HTTP error {e.code}: {error_data!r}')

            if e.code == 404:
                return None

            raise
    except Exception as e:
        raise InstallerError(
            f'Could not fetch information on the {package_name} packages '
            f'(at {url}). Check your network and HTTP(S) proxy environment '
            f'variables (`http_proxy` and `https_proxy`). The error was: '
            f'{e}'
        )

    python_version = '%s.%s.%s' % system_info['system_python_version'][:3]

    try:
        rsp_info = rsp['info']
        latest_version = rsp_info['version']
        parsed_latest_version = parse_version(latest_version)

        if target_version == 'latest':
            target_version = latest_version

        parsed_target_version = parse_version(target_version)

        # Find the nearest compatible version of Review Board.
        rsp_releases = sorted(
            rsp['releases'].items(),
            key=lambda pair: parse_version(pair[0]),
            reverse=True)

        debug(f'Found {len(rsp_releases)} possible releases for '
              f'"{package_name}".')

        for rsp_version, rsp_release in rsp_releases:
            if not rsp_release:
                continue

            parsed_rsp_version = parse_version(rsp_version)

            if parsed_rsp_version > parsed_target_version:
                continue

            rsp_dist = rsp_release[0]

            if rsp_dist.get('yanked'):
                continue

            requires_python = rsp_dist.get('requires_python', '')

            if (not requires_python or
                python_version in SpecifierSet(requires_python)):
                # This is a compatible version. Return it.
                debug(f'Found compatible release for "{package_name}": '
                      f'{parsed_rsp_version}')

                return {
                    'is_latest': parsed_rsp_version == parsed_latest_version,
                    'is_requested':
                        parsed_rsp_version == parsed_target_version,
                    'latest_version': latest_version,
                    'package_name': rsp_info['name'],
                    'requires_python': requires_python,
                    'version': rsp_version,
                }

        debug(f'Could not find compatible release for "{package_name}".')

        return None
    except Exception as e:
        raise InstallerError(
            f'Could not parse information on {package_name} packages '
            f'(at {url}). This may indicate an issue accessing '
            f'https://pypi.org/ or an issue with the requested version of '
            f'Review Board. The error was: {e}'
        )
