"""Unit tests for rbinstall.state.

Version Added:
    1.0
"""

from __future__ import annotations

import os
import platform
import re
import subprocess
import sys
import tempfile
from unittest import TestCase

import kgb

from rbinstall.errors import InstallerError
from rbinstall.install_methods import InstallMethodType
from rbinstall.state import (get_default_linux_install_method,
                             get_system_info)


class GetSystemInfoTests(kgb.SpyAgency, TestCase):
    """Unit tests for get_system_info().

    Version Added:
        1.0
    """

    EMPTY_ENVIRON = {
        'RBINSTALL_FORCE_ARCH': '',
        'RBINSTALL_FORCE_SYSTEM': '',
        'RBINSTALL_FORCE_SYSTEM_PYTHON_EXE': '',
        'RBINSTALL_OS_RELEASE_FILE': '',
    }

    maxDiff = None

    def setUp(self) -> None:
        super().setUp()

        os.environ.update(self.EMPTY_ENVIRON)

    def tearDown(self) -> None:
        super().tearDown()

        os.environ.update(self.EMPTY_ENVIRON)

    def test_with_linux(self) -> None:
        """Testing get_system_info with Linux"""
        fd, os_release_path = tempfile.mkstemp()

        with os.fdopen(fd, 'w') as fp:
            fp.write('ID="mydistro"\n')
            fp.write('ID_LIKE="centos rhel fedora"\n')
            fp.write('NAME="MyDistro"\n')
            fp.write('PRETTY_NAME="My Distro"\n')
            fp.write('VERSION_ID="1.2.3"\n')

        try:
            os.environ.update({
                'RBINSTALL_FORCE_ARCH': 'amd64',
                'RBINSTALL_FORCE_SYSTEM': 'Linux',
                'RBINSTALL_FORCE_SYSTEM_PYTHON_EXE': '/path/to/python',
                'RBINSTALL_OS_RELEASE_FILE': os_release_path,
            })
            system_info = get_system_info()
        finally:
            os.unlink(os_release_path)

        self.assertEqual(
            system_info,
            {
                'arch': 'amd64',
                'bootstrap_python_exe': sys.executable,
                'distro_families': {
                    'centos',
                    'fedora',
                    'mydistro',
                    'rhel',
                },
                'distro_full_name': 'My Distro',
                'distro_id': 'mydistro',
                'distro_name': 'MyDistro',
                'paths': {},
                'system': 'Linux',
                'system_install_method': InstallMethodType.YUM,
                'system_python_exe': '/path/to/python',
                'system_python_version': sys.version_info,
                'version': '1.2.3',
            })

    def test_with_linux_minimal_distro_info(self) -> None:
        """Testing get_system_info with Linux and minimal distro information
        """
        fd, os_release_path = tempfile.mkstemp()

        with os.fdopen(fd, 'w') as fp:
            fp.write('ID="rhel"\n')

        try:
            os.environ.update({
                'RBINSTALL_FORCE_ARCH': 'amd64',
                'RBINSTALL_FORCE_SYSTEM': 'Linux',
                'RBINSTALL_FORCE_SYSTEM_PYTHON_EXE': '/path/to/python',
                'RBINSTALL_OS_RELEASE_FILE': os_release_path,
            })
            system_info = get_system_info()
        finally:
            os.unlink(os_release_path)

        self.assertEqual(
            system_info,
            {
                'arch': 'amd64',
                'bootstrap_python_exe': sys.executable,
                'distro_families': {'rhel'},
                'distro_full_name': None,
                'distro_id': 'rhel',
                'distro_name': None,
                'paths': {},
                'system': 'Linux',
                'system_install_method': InstallMethodType.YUM,
                'system_python_exe': '/path/to/python',
                'system_python_version': sys.version_info,
                'version': '',
            })

    def test_with_linux_and_no_distro_info(self) -> None:
        """Testing get_system_info with Linux and no distro information"""
        fd, os_release_path = tempfile.mkstemp()

        message = re.escape(
            'Could not determine the distribution of Linux being used. This '
            'indicates you may be missing /etc/os-release and '
            '/usr/lib/os-release files. You may need to install through '
            'another method. See https://www.reviewboard.org/docs/manual/'
            'latest/admin/installation/ for instructions.'
        )

        try:
            os.environ.update({
                'RBINSTALL_FORCE_ARCH': 'amd64',
                'RBINSTALL_FORCE_SYSTEM': 'Linux',
                'RBINSTALL_FORCE_SYSTEM_PYTHON_EXE': '/path/to/python',
                'RBINSTALL_OS_RELEASE_FILE': os_release_path,
            })

            with self.assertRaisesRegex(InstallerError, message):
                get_system_info()
        finally:
            os.unlink(os_release_path)

    def test_with_linux_and_incompatible_family(self) -> None:
        """Testing get_system_info with Linux and incompatible family"""
        fd, os_release_path = tempfile.mkstemp()

        with os.fdopen(fd, 'w') as fp:
            fp.write('ID="mydistro"\n')
            fp.write('ID_LIKE="whoknows"\n')

        message = re.escape(
            "The Review Board installer doesn't support installing on this "
            "family of Linux (mydistro, whoknows). Please contact "
            "support@beanbaginc.com for assistance. You may need to install "
            "through another method. See https://www.reviewboard.org/docs/"
            "manual/latest/admin/installation/ for instructions."
        )

        try:
            os.environ.update({
                'RBINSTALL_FORCE_ARCH': 'amd64',
                'RBINSTALL_FORCE_SYSTEM': 'Linux',
                'RBINSTALL_FORCE_SYSTEM_PYTHON_EXE': '/path/to/python',
                'RBINSTALL_OS_RELEASE_FILE': os_release_path,
            })

            with self.assertRaisesRegex(InstallerError, message):
                get_system_info()
        finally:
            os.unlink(os_release_path)

    def test_with_darwin_and_brew(self) -> None:
        """Testing get_system_info with Darwin and brew"""
        self.spy_on(platform.mac_ver,
                    op=kgb.SpyOpReturn(('13.5.2', ('', '', ''), 'arm64')))
        self.spy_on(subprocess.check_output,
                    op=kgb.SpyOpReturn(b'/opt/homebrew\n'))

        os.environ.update({
            'RBINSTALL_FORCE_ARCH': 'arm64',
            'RBINSTALL_FORCE_SYSTEM': 'Darwin',
            'RBINSTALL_FORCE_SYSTEM_PYTHON_EXE': '/path/to/python',
        })

        system_info = get_system_info()

        self.assertEqual(
            system_info,
            {
                'arch': 'arm64',
                'bootstrap_python_exe': sys.executable,
                'paths': {
                    'brew': '/opt/homebrew',
                },
                'system': 'Darwin',
                'system_install_method': InstallMethodType.BREW,
                'system_python_exe': '/path/to/python',
                'system_python_version': sys.version_info,
                'version': '13.5.2',
            })

    def test_with_darwin_and_no_brew(self) -> None:
        """Testing get_system_info with Darwin and no brew"""
        self.spy_on(platform.mac_ver,
                    op=kgb.SpyOpReturn(('13.5.2', ('', '', ''), 'arm64')))
        self.spy_on(subprocess.check_output,
                    op=kgb.SpyOpRaise(subprocess.CalledProcessError(
                        returncode=1,
                        cmd=['brew', '--prefix'])))

        os.environ.update({
            'RBINSTALL_FORCE_ARCH': 'arm64',
            'RBINSTALL_FORCE_SYSTEM': 'Darwin',
            'RBINSTALL_FORCE_SYSTEM_PYTHON_EXE': '/path/to/python',
        })

        message = re.escape(
            'The Review Board installer cannot install on macOS without '
            'Brew (https://brew.sh). You may need to install through another '
            'method. See https://www.reviewboard.org/docs/manual/latest/'
            'admin/installation/ for instructions.'
        )

        with self.assertRaisesRegex(InstallerError, message):
            get_system_info()

    def test_with_unsupported_platform(self) -> None:
        """Testing get_system_info with unsupported platform"""
        os.environ.update({
            'RBINSTALL_FORCE_ARCH': 'arm64',
            'RBINSTALL_FORCE_SYSTEM': 'WhoKnows',
        })

        message = re.escape(
            'Review Board can only be installed in Linux or macOS using '
            'this installation script. You may need to install through '
            'another method. See https://www.reviewboard.org/docs/manual/'
            'latest/admin/installation/ for instructions.'
        )

        with self.assertRaisesRegex(InstallerError, message):
            get_system_info()


class GetDefaultLinuxInstallMethodTests(TestCase):
    """Unit tests for get_default_linux_install_method()."""

    def test_with_arch(self) -> None:
        """Testing get_default_linux_install_method with 'arch'"""
        self.assertEqual(
            get_default_linux_install_method(families={'arch'}),
            InstallMethodType.PACMAN)

    def test_with_debian(self) -> None:
        """Testing get_default_linux_install_method with 'debian'"""
        self.assertEqual(
            get_default_linux_install_method(families={'debian'}),
            InstallMethodType.APT)

    def test_with_fedora(self) -> None:
        """Testing get_default_linux_install_method with 'fedora'"""
        self.assertEqual(
            get_default_linux_install_method(families={'fedora'}),
            InstallMethodType.YUM)

    def test_with_opensuse(self) -> None:
        """Testing get_default_linux_install_method with 'opensuse'"""
        self.assertEqual(
            get_default_linux_install_method(families={'opensuse'}),
            InstallMethodType.ZYPPER)

    def test_with_rhel(self) -> None:
        """Testing get_default_linux_install_method with 'rhel'"""
        self.assertEqual(
            get_default_linux_install_method(families={'rhel'}),
            InstallMethodType.YUM)
