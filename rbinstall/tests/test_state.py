"""Unit tests for rbinstall.state.

Version Added:
    1.0
"""

from __future__ import annotations

from datetime import date

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
                             get_system_info,
                             is_eol_distro)


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


class TestEOLDistro(TestCase):
    """Unit tests for is_eol_distro().

    Version Added:
        1.3
    """

    # EOL distros
    def test_with_amzn_2(self) -> None:
        """Testing is_eol_distro with Amazon Linux 2"""
        self.assertTrue(is_eol_distro(
            self._make_system_info('amzn', '2'),
            now=date(2026, 7, 1)))

    def test_with_amzn_1(self) -> None:
        """Testing is_eol_distro with Amazon Linux 1"""
        self.assertTrue(is_eol_distro(
            self._make_system_info('amzn', '1'),
            now=date(2026, 7, 1)))

    def test_with_centos_8(self) -> None:
        """Testing is_eol_distro with CentOS 8"""
        self.assertTrue(is_eol_distro(
            self._make_system_info('centos', '8'),
            now=date(2024, 6, 1)))

    def test_with_centos_7(self) -> None:
        """Testing is_eol_distro with CentOS 7"""
        self.assertTrue(is_eol_distro(
            self._make_system_info('centos', '7'),
            now=date(2024, 6, 1)))

    def test_with_debian_10(self) -> None:
        """Testing is_eol_distro with Debian 10"""
        self.assertTrue(is_eol_distro(
            self._make_system_info('debian', '10'),
            now=date(2022, 10, 1)))

    def test_with_debian_9(self) -> None:
        """Testing is_eol_distro with Debian 9"""
        self.assertTrue(is_eol_distro(
            self._make_system_info('debian', '9'),
            now=date(2022, 10, 1)))

    def test_with_fedora_36(self) -> None:
        """Testing is_eol_distro with Fedora 36"""
        self.assertTrue(is_eol_distro(
            self._make_system_info('fedora', '36'),
            now=date(2025, 12, 16)))

    def test_with_fedora_39(self) -> None:
        """Testing is_eol_distro with Fedora 39"""
        self.assertTrue(is_eol_distro(
            self._make_system_info('fedora', '39'),
            now=date(2025, 12, 16)))

    def test_with_ubuntu_18_04(self) -> None:
        """Testing is_eol_distro with Ubuntu 18.04"""
        self.assertTrue(is_eol_distro(
            self._make_system_info('ubuntu', '18.04'),
            now=date(2023, 6, 1)))

    def test_with_ubuntu_23_10(self) -> None:
        """Testing is_eol_distro with Ubuntu 23.10"""
        self.assertTrue(is_eol_distro(
            self._make_system_info('ubuntu', '23.10'),
            now=date(2026, 2, 1)))

    def test_with_ubuntu_21_04(self) -> None:
        """Testing is_eol_distro with Ubuntu 21.04"""
        self.assertTrue(is_eol_distro(
            self._make_system_info('ubuntu', '21.04'),
            now=date(2026, 2, 1)))

    # Non-EOL distros
    def test_with_amzn_2023(self) -> None:
        """Testing is_eol_distro with Amazon Linux 2023"""
        self.assertFalse(is_eol_distro(
            self._make_system_info('amzn', '2023'),
            now=date(2029, 1, 1)))

    def test_with_centos_9(self) -> None:
        """Testing is_eol_distro with CentOS 9"""
        self.assertFalse(is_eol_distro(
            self._make_system_info('centos', '9'),
            now=date(2027, 1, 1)))

    def test_with_debian_12(self) -> None:
        """Testing is_eol_distro with Debian 12"""
        self.assertFalse(is_eol_distro(
            self._make_system_info('debian', '12'),
            now=date(2026, 1, 1)))

    def test_with_fedora_40(self) -> None:
        """Testing is_eol_distro with Fedora 40"""
        self.assertFalse(is_eol_distro(
            self._make_system_info('fedora', '40'),
            now=date(2025, 1, 1)))

    def test_with_ubuntu_20_04(self) -> None:
        """Testing is_eol_distro with Ubuntu 20.04"""
        self.assertFalse(is_eol_distro(
            self._make_system_info('ubuntu', '20.04'),
            now=date(2025, 1, 1)))

    def test_with_ubuntu_22_04(self) -> None:
        """Testing is_eol_distro with Ubuntu 22.04"""
        self.assertFalse(is_eol_distro(
            self._make_system_info('ubuntu', '22.04'),
            now=date(2027, 1, 1)))

    def test_with_ubuntu_24_04(self) -> None:
        """Testing is_eol_distro with Ubuntu 24.04"""
        self.assertFalse(is_eol_distro(
            self._make_system_info('ubuntu', '24.04'),
            now=date(2029, 1, 1)))

    def test_with_ubuntu_25_10(self) -> None:
        """Testing is_eol_distro with Ubuntu 25.10"""
        self.assertFalse(is_eol_distro(
            self._make_system_info('ubuntu', '25.10'),
            now=date(2026, 1, 1)))

    # Boundary conditions
    def test_with_eol_on_exact_date(self) -> None:
        """Testing is_eol_distro on the exact EOL date"""
        self.assertTrue(is_eol_distro(
            self._make_system_info('debian', '12'),
            now=date(2026, 6, 10)))

    def test_with_eol_one_day_before(self) -> None:
        """Testing is_eol_distro one day before the EOL date"""
        self.assertFalse(is_eol_distro(
            self._make_system_info('debian', '12'),
            now=date(2026, 6, 9)))

    # Evergreen distros
    def test_with_arch(self) -> None:
        """Testing is_eol_distro with Arch Linux (evergreen)"""
        self.assertFalse(is_eol_distro(
            self._make_system_info('arch', '2024.01.01'),
            now=date(2040, 1, 1)))

    def test_with_opensuse_tumbleweed(self) -> None:
        """Testing is_eol_distro with openSUSE Tumbleweed (evergreen)"""
        self.assertFalse(is_eol_distro(
            self._make_system_info('opensuse-tumbleweed', '20240101'),
            now=date(2040, 1, 1)))

    # openSUSE Leap
    def test_with_opensuse_leap_42(self) -> None:
        """Testing is_eol_distro with openSUSE Leap 42 (mislabeled v14)"""
        self.assertTrue(is_eol_distro(
            self._make_system_info('opensuse-leap', '42.3'),
            now=date(2019, 8, 1)))

    def test_with_opensuse_leap_15_4(self) -> None:
        """Testing is_eol_distro with openSUSE Leap 15.4"""
        self.assertTrue(is_eol_distro(
            self._make_system_info('opensuse-leap', '15.4'),
            now=date(2025, 1, 1)))

    def test_with_opensuse_leap_15_6(self) -> None:
        """Testing is_eol_distro with openSUSE Leap 15.6"""
        self.assertFalse(is_eol_distro(
            self._make_system_info('opensuse-leap', '15.6'),
            now=date(2026, 1, 1)))

    # Unknown future version
    def test_with_unknown_future_version(self) -> None:
        """Testing is_eol_distro with a future Fedora version not in data"""
        self.assertFalse(is_eol_distro(
            self._make_system_info('fedora', '99'),
            now=date(2040, 1, 1)))

    # Edge cases
    def test_with_missing_distro_id(self) -> None:
        """Testing is_eol_distro with missing distro_id"""
        self.assertFalse(is_eol_distro({
            'version': '10',
        }))

    def test_with_missing_version(self) -> None:
        """Testing is_eol_distro with missing version"""
        self.assertFalse(is_eol_distro({
            'distro_id': 'debian',
        }))

    def test_with_empty_version(self) -> None:
        """Testing is_eol_distro with empty version"""
        self.assertFalse(is_eol_distro(
            self._make_system_info('debian', '')))

    def test_with_unknown_distro(self) -> None:
        """Testing is_eol_distro with unknown distro"""
        self.assertFalse(is_eol_distro(
            self._make_system_info('archlinux', '2024.01.01')))

    def _make_system_info(
        self,
        distro_id: str,
        version: str,
    ) -> dict:
        """Return a minimal SystemInfo-like dict for testing.

        Args:
            distro_id (str):
                The distribution ID.

            version (str):
                The version string.

        Returns:
            dict:
            A dictionary with ``distro_id`` and ``version`` keys.
        """
        return {
            'distro_id': distro_id,
            'version': version,
        }
