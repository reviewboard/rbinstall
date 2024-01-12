"""Unit tests for rbinstall.install_steps.

Version Added:
    1.0
"""

from __future__ import annotations

from typing import Set, TYPE_CHECKING
from unittest import TestCase

from rbinstall.install_methods import InstallMethodType
from rbinstall.install_steps import get_install_steps
from rbinstall.state import get_default_linux_install_method

if TYPE_CHECKING:
    from rbinstall.state import InstallState


class GetInstallSteps(TestCase):
    """Unit tests for get_install_steps().

    Version Added:
        1.0
    """

    maxDiff = None

    VIRTUALENV_STEPS = [
        {
            'install_method': InstallMethodType.SHELL,
            'name': 'Creating Python virtual environment',
            'state': [
                '/path/to/bootstrap/python',
                '-m',
                'virtualenv',
                '--download',
                '-p',
                '/usr/bin/python',
                '/path/to/venv',
            ],
        },
        {
            'allow_fail': False,
            'install_method': InstallMethodType.PIP,
            'name': 'Installing Python packaging support',
            'state': ['pip', 'setuptools', 'wheel'],
        },
    ]

    PYSVN_STEPS = [
        {
            'allow_fail': False,
            'install_method': InstallMethodType.REMOTE_PYSCRIPT,
            'name': 'Installing service integrations',
            'state': ['https://pysvn.reviewboard.org'],
        },
    ]

    RB_STEPS = [
        {
            'install_method': InstallMethodType.PIP,
            'name': 'Installing Review Board packages',
            'state': [
                'ReviewBoard==6.0',
                'ReviewBoardPowerPack==5.2.2',
                'reviewbot-extension==4.0',
                'reviewbot-worker==4.0',
            ],
        },
        {
            'allow_fail': False,
            'install_method': InstallMethodType.REVIEWBOARD_EXTRA,
            'name': 'Installing service integrations',
            'state': [
                's3',
                'swift',
                'mercurial',
                'mysql',
                'postgres',
            ],
        },
    ]

    COMMON_X86_STEPS = [
        *VIRTUALENV_STEPS,
        *RB_STEPS,
        *PYSVN_STEPS,
    ]

    COMMON_ARM64_STEPS = [
        *VIRTUALENV_STEPS,
        *RB_STEPS,
        {
            'allow_fail': True,
            'install_method': InstallMethodType.REVIEWBOARD_EXTRA,
            'name': 'Installing service integrations',
            'state': [
                'p4',
            ],
        },
        *PYSVN_STEPS,
    ]

    def test_with_amazon_linux_2_x86_64(self) -> None:
        """Testing get_install_steps with Amazon Linux 2 (x86_64)"""
        install_state = self.create_install_state(
            arch='x86_64',
            distro_id='amzn',
            distro_families={
                'amzn',
                'centos',
                'fedora',
                'rhel',
            },
            version='2')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'yum', 'groupinstall', '-y', 'Development Tools',
                    ],
                },
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.YUM,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc',
                        'gcc-c++',
                        'libffi-devel',
                        'libxml2-devel',
                        'make',
                        'openssl-devel',
                        'patch',
                        'perl',
                        'python3-devel',
                        'libtool-ltdl-devel',
                        'cvs',
                        'git',
                        'memcached',
                        'mariadb-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_ARM64_STEPS,
            ])

    def test_with_amazon_linux_2_aarch64(self) -> None:
        """Testing get_install_steps with Amazon Linux 2 (aarch64)"""
        install_state = self.create_install_state(
            arch='aarch64',
            distro_id='amzn',
            distro_families={
                'amzn',
                'centos',
                'fedora',
                'rhel',
            },
            version='2')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'yum', 'groupinstall', '-y', 'Development Tools',
                    ],
                },
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.YUM,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc',
                        'gcc-c++',
                        'libffi-devel',
                        'libxml2-devel',
                        'make',
                        'openssl-devel',
                        'patch',
                        'perl',
                        'python3-devel',
                        'libtool-ltdl-devel',
                        'cvs',
                        'git',
                        'memcached',
                        'mariadb-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_X86_STEPS,
            ])

    def test_with_amazon_linux_2023_x86_64(self) -> None:
        """Testing get_install_steps with Amazon Linux 2023 (x86_64)"""
        install_state = self.create_install_state(
            arch='x86_64',
            distro_id='amzn',
            distro_families={
                'amzn',
                'fedora',
            },
            version='2023')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.YUM,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc',
                        'gcc-c++',
                        'libffi-devel',
                        'libxml2-devel',
                        'make',
                        'openssl-devel',
                        'patch',
                        'perl',
                        'python3-devel',
                        'libtool-ltdl-devel',
                        'cvs',
                        'git',
                        'memcached',
                        'mariadb-connector-c-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_ARM64_STEPS,
            ])

    def test_with_amazon_linux_2023_aarch64(self) -> None:
        """Testing get_install_steps with Amazon Linux 2023 (aarch64)"""
        install_state = self.create_install_state(
            arch='aarch64',
            distro_id='amzn',
            distro_families={
                'amzn',
                'fedora',
            },
            version='2023')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.YUM,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc',
                        'gcc-c++',
                        'libffi-devel',
                        'libxml2-devel',
                        'make',
                        'openssl-devel',
                        'patch',
                        'perl',
                        'python3-devel',
                        'libtool-ltdl-devel',
                        'cvs',
                        'git',
                        'memcached',
                        'mariadb-connector-c-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_X86_STEPS,
            ])

    def test_with_archlinux_2023_x86_64(self) -> None:
        """Testing get_install_steps with Arch Linux (x86_64)"""
        install_state = self.create_install_state(
            arch='x86_64',
            distro_id='arch',
            distro_families={
                'arch',
            },
            version='20231112.0.191179')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.PACMAN,
                    'name': 'Installing system packages',
                    'state': [
                        'base-devel',
                        'libffi',
                        'libxml2',
                        'openssl',
                        'perl',
                        'xmlsec',
                        'cvs',
                        'git',
                        'memcached',
                        'mariadb-libs',
                        'subversion',
                    ],
                },
                *self.COMMON_ARM64_STEPS,
            ])

    def test_with_archlinux_2023_aarch64(self) -> None:
        """Testing get_install_steps with Arch Linux (aarch64)"""
        install_state = self.create_install_state(
            arch='aarch64',
            distro_id='arch',
            distro_families={
                'arch',
            },
            version='20231112.0.191179')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.PACMAN,
                    'name': 'Installing system packages',
                    'state': [
                        'base-devel',
                        'libffi',
                        'libxml2',
                        'openssl',
                        'perl',
                        'xmlsec',
                        'cvs',
                        'git',
                        'memcached',
                        'mariadb-libs',
                        'subversion',
                    ],
                },
                *self.COMMON_X86_STEPS,
            ])

    def test_with_centos_stream_8_x86_64(self) -> None:
        """Testing get_install_steps with CentOS Stream 8 (x86_64)"""
        install_state = self.create_install_state(
            arch='x86_64',
            distro_id='centos',
            distro_families={
                'centos',
                'fedora',
                'rhel',
            },
            version='8')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'dnf', 'install', '-y', 'dnf-plugins-core',
                    ],
                },
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'dnf', 'config-manager', '--set-enabled', 'crb',
                    ],
                },
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'yum', 'install', '-y', 'epel-release',
                        'epel-next-release',
                    ],
                },
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.YUM,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc',
                        'gcc-c++',
                        'libffi-devel',
                        'libxml2-devel',
                        'make',
                        'openssl-devel',
                        'patch',
                        'perl',
                        'python3-devel',
                        'libtool-ltdl-devel',
                        'cvs',
                        'git',
                        'memcached',
                        'mariadb-connector-c-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_ARM64_STEPS,
            ])

    def test_with_centos_stream_8_aarch64(self) -> None:
        """Testing get_install_steps with CentOS Stream 8 (aarch64)"""
        install_state = self.create_install_state(
            arch='aarch64',
            distro_id='centos',
            distro_families={
                'centos',
                'fedora',
                'rhel',
            },
            version='8')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'dnf', 'install', '-y', 'dnf-plugins-core',
                    ],
                },
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'dnf', 'config-manager', '--set-enabled', 'crb',
                    ],
                },
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'yum', 'install', '-y', 'epel-release',
                        'epel-next-release',
                    ],
                },
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.YUM,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc',
                        'gcc-c++',
                        'libffi-devel',
                        'libxml2-devel',
                        'make',
                        'openssl-devel',
                        'patch',
                        'perl',
                        'python3-devel',
                        'libtool-ltdl-devel',
                        'cvs',
                        'git',
                        'memcached',
                        'mariadb-connector-c-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_X86_STEPS,
            ])

    def test_with_centos_stream_9_x86_64(self) -> None:
        """Testing get_install_steps with CentOS Stream 9 (x86_64)"""
        install_state = self.create_install_state(
            arch='x86_64',
            distro_id='centos',
            distro_families={
                'centos',
                'fedora',
                'rhel',
            },
            version='9')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'dnf', 'install', '-y', 'dnf-plugins-core',
                    ],
                },
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'dnf', 'config-manager', '--set-enabled', 'crb',
                    ],
                },
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'yum', 'install', '-y', 'epel-release',
                        'epel-next-release',
                    ],
                },
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.YUM,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc',
                        'gcc-c++',
                        'libffi-devel',
                        'libxml2-devel',
                        'make',
                        'openssl-devel',
                        'patch',
                        'perl',
                        'python3-devel',
                        'libtool-ltdl-devel',
                        'cvs',
                        'git',
                        'memcached',
                        'mariadb-connector-c-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_ARM64_STEPS,
            ])

    def test_with_centos_stream_9_aarch64(self) -> None:
        """Testing get_install_steps with CentOS Stream 9 (aarch64)"""
        install_state = self.create_install_state(
            arch='aarch64',
            distro_id='centos',
            distro_families={
                'centos',
                'fedora',
                'rhel',
            },
            version='9')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'dnf', 'install', '-y', 'dnf-plugins-core',
                    ],
                },
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'dnf', 'config-manager', '--set-enabled', 'crb',
                    ],
                },
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'yum', 'install', '-y', 'epel-release',
                        'epel-next-release',
                    ],
                },
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.YUM,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc',
                        'gcc-c++',
                        'libffi-devel',
                        'libxml2-devel',
                        'make',
                        'openssl-devel',
                        'patch',
                        'perl',
                        'python3-devel',
                        'libtool-ltdl-devel',
                        'cvs',
                        'git',
                        'memcached',
                        'mariadb-connector-c-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_X86_STEPS,
            ])

    def test_with_debian_11_x86_64(self) -> None:
        """Testing get_install_steps with Debian 11 (x86_64)"""
        install_state = self.create_install_state(
            arch='x86_64',
            distro_id='debian',
            distro_families={
                'debian',
            },
            version='11 (bullseye)')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.APT,
                    'name': 'Installing system packages',
                    'state': [
                        'build-essential',
                        'libffi-dev',
                        'libjpeg-dev',
                        'libssl-dev',
                        'libxml2-dev',
                        'libxmlsec1-dev',
                        'libxmlsec1-openssl',
                        'patch',
                        'pkg-config',
                        'python3-dev',
                        'python3-pip',
                        'cvs',
                        'git',
                        'memcached',
                        'libmariadb-dev',
                        'subversion',
                        'libsvn-dev',
                    ],
                },
                *self.COMMON_ARM64_STEPS,
            ])

    def test_with_debian_11_aarch64(self) -> None:
        """Testing get_install_steps with Debian 11 (aarch64)"""
        install_state = self.create_install_state(
            arch='aarch64',
            distro_id='debian',
            distro_families={
                'debian',
            },
            version='11 (bullseye)')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.APT,
                    'name': 'Installing system packages',
                    'state': [
                        'build-essential',
                        'libffi-dev',
                        'libjpeg-dev',
                        'libssl-dev',
                        'libxml2-dev',
                        'libxmlsec1-dev',
                        'libxmlsec1-openssl',
                        'patch',
                        'pkg-config',
                        'python3-dev',
                        'python3-pip',
                        'cvs',
                        'git',
                        'memcached',
                        'libmariadb-dev',
                        'subversion',
                        'libsvn-dev',
                    ],
                },
                *self.COMMON_X86_STEPS,
            ])

    def test_with_debian_12_x86_64(self) -> None:
        """Testing get_install_steps with Debian 12 (x86_64)"""
        install_state = self.create_install_state(
            arch='x86_64',
            distro_id='debian',
            distro_families={
                'debian',
            },
            version='12 (bookworm)')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.APT,
                    'name': 'Installing system packages',
                    'state': [
                        'build-essential',
                        'libffi-dev',
                        'libjpeg-dev',
                        'libssl-dev',
                        'libxml2-dev',
                        'libxmlsec1-dev',
                        'libxmlsec1-openssl',
                        'patch',
                        'pkg-config',
                        'python3-dev',
                        'python3-pip',
                        'cvs',
                        'git',
                        'memcached',
                        'libmariadb-dev',
                        'subversion',
                        'libsvn-dev',
                    ],
                },
                *self.COMMON_ARM64_STEPS,
            ])

    def test_with_debian_12_aarch64(self) -> None:
        """Testing get_install_steps with Debian 12 (aarch64)"""
        install_state = self.create_install_state(
            arch='aarch64',
            distro_id='debian',
            distro_families={
                'debian',
            },
            version='12 (bookworm)')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.APT,
                    'name': 'Installing system packages',
                    'state': [
                        'build-essential',
                        'libffi-dev',
                        'libjpeg-dev',
                        'libssl-dev',
                        'libxml2-dev',
                        'libxmlsec1-dev',
                        'libxmlsec1-openssl',
                        'patch',
                        'pkg-config',
                        'python3-dev',
                        'python3-pip',
                        'cvs',
                        'git',
                        'memcached',
                        'libmariadb-dev',
                        'subversion',
                        'libsvn-dev',
                    ],
                },
                *self.COMMON_X86_STEPS,
            ])

    def test_with_fedora_36_x86_64(self) -> None:
        """Testing get_install_steps with Fedora 36 (x86_64)"""
        install_state = self.create_install_state(
            arch='x86_64',
            distro_id='fedora',
            distro_families={
                'fedora',
            },
            version='36')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.YUM,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc',
                        'gcc-c++',
                        'libffi-devel',
                        'libxml2-devel',
                        'make',
                        'openssl-devel',
                        'patch',
                        'perl',
                        'python3-devel',
                        'libtool-ltdl-devel',
                        'cvs',
                        'git',
                        'memcached',
                        'mariadb-connector-c-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_ARM64_STEPS,
            ])

    def test_with_fedora_36_aarch64(self) -> None:
        """Testing get_install_steps with Fedora 36 (aarch64)"""
        install_state = self.create_install_state(
            arch='aarch64',
            distro_id='fedora',
            distro_families={
                'fedora',
            },
            version='36')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.YUM,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc',
                        'gcc-c++',
                        'libffi-devel',
                        'libxml2-devel',
                        'make',
                        'openssl-devel',
                        'patch',
                        'perl',
                        'python3-devel',
                        'libtool-ltdl-devel',
                        'cvs',
                        'git',
                        'memcached',
                        'mariadb-connector-c-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_X86_STEPS,
            ])

    def test_with_fedora_37_x86_64(self) -> None:
        """Testing get_install_steps with Fedora 37 (x86_64)"""
        install_state = self.create_install_state(
            arch='x86_64',
            distro_id='fedora',
            distro_families={
                'fedora',
            },
            version='37')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.YUM,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc',
                        'gcc-c++',
                        'libffi-devel',
                        'libxml2-devel',
                        'make',
                        'openssl-devel',
                        'patch',
                        'perl',
                        'python3-devel',
                        'libtool-ltdl-devel',
                        'cvs',
                        'git',
                        'memcached',
                        'mariadb-connector-c-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_ARM64_STEPS,
            ])

    def test_with_fedora_37_aarch64(self) -> None:
        """Testing get_install_steps with Fedora 37 (aarch64)"""
        install_state = self.create_install_state(
            arch='aarch64',
            distro_id='fedora',
            distro_families={
                'fedora',
            },
            version='37')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.YUM,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc',
                        'gcc-c++',
                        'libffi-devel',
                        'libxml2-devel',
                        'make',
                        'openssl-devel',
                        'patch',
                        'perl',
                        'python3-devel',
                        'libtool-ltdl-devel',
                        'cvs',
                        'git',
                        'memcached',
                        'mariadb-connector-c-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_X86_STEPS,
            ])

    def test_with_fedora_38_x86_64(self) -> None:
        """Testing get_install_steps with Fedora 38 (x86_64)"""
        install_state = self.create_install_state(
            arch='x86_64',
            distro_id='fedora',
            distro_families={
                'fedora',
            },
            version='38')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.YUM,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc',
                        'gcc-c++',
                        'libffi-devel',
                        'libxml2-devel',
                        'make',
                        'openssl-devel',
                        'patch',
                        'perl',
                        'python3-devel',
                        'libtool-ltdl-devel',
                        'cvs',
                        'git',
                        'memcached',
                        'mariadb-connector-c-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_ARM64_STEPS,
            ])

    def test_with_fedora_38_aarch64(self) -> None:
        """Testing get_install_steps with Fedora 38 (aarch64)"""
        install_state = self.create_install_state(
            arch='aarch64',
            distro_id='fedora',
            distro_families={
                'fedora',
            },
            version='38')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.YUM,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc',
                        'gcc-c++',
                        'libffi-devel',
                        'libxml2-devel',
                        'make',
                        'openssl-devel',
                        'patch',
                        'perl',
                        'python3-devel',
                        'libtool-ltdl-devel',
                        'cvs',
                        'git',
                        'memcached',
                        'mariadb-connector-c-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_X86_STEPS,
            ])

    def test_with_fedora_39_x86_64(self) -> None:
        """Testing get_install_steps with Fedora 39 (x86_64)"""
        install_state = self.create_install_state(
            arch='x86_64',
            distro_id='fedora',
            distro_families={
                'fedora',
            },
            version='39')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.YUM,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc',
                        'gcc-c++',
                        'libffi-devel',
                        'libxml2-devel',
                        'make',
                        'openssl-devel',
                        'patch',
                        'perl',
                        'python3-devel',
                        'libtool-ltdl-devel',
                        'cvs',
                        'git',
                        'memcached',
                        'mariadb-connector-c-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_ARM64_STEPS,
            ])

    def test_with_fedora_39_aarch64(self) -> None:
        """Testing get_install_steps with Fedora 39 (aarch64)"""
        install_state = self.create_install_state(
            arch='aarch64',
            distro_id='fedora',
            distro_families={
                'fedora',
            },
            version='39')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.YUM,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc',
                        'gcc-c++',
                        'libffi-devel',
                        'libxml2-devel',
                        'make',
                        'openssl-devel',
                        'patch',
                        'perl',
                        'python3-devel',
                        'libtool-ltdl-devel',
                        'cvs',
                        'git',
                        'memcached',
                        'mariadb-connector-c-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_X86_STEPS,
            ])

    def test_with_fedora_40_x86_64(self) -> None:
        """Testing get_install_steps with Fedora 40 (x86_64)"""
        install_state = self.create_install_state(
            arch='x86_64',
            distro_id='fedora',
            distro_families={
                'fedora',
            },
            version='40')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.YUM,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc',
                        'gcc-c++',
                        'libffi-devel',
                        'libxml2-devel',
                        'make',
                        'openssl-devel',
                        'patch',
                        'perl',
                        'python3-devel',
                        'libtool-ltdl-devel',
                        'cvs',
                        'git',
                        'memcached',
                        'mariadb-connector-c-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_ARM64_STEPS,
            ])

    def test_with_fedora_40_aarch64(self) -> None:
        """Testing get_install_steps with Fedora 40 (aarch64)"""
        install_state = self.create_install_state(
            arch='aarch64',
            distro_id='fedora',
            distro_families={
                'fedora',
            },
            version='40')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.YUM,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc',
                        'gcc-c++',
                        'libffi-devel',
                        'libxml2-devel',
                        'make',
                        'openssl-devel',
                        'patch',
                        'perl',
                        'python3-devel',
                        'libtool-ltdl-devel',
                        'cvs',
                        'git',
                        'memcached',
                        'mariadb-connector-c-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_X86_STEPS,
            ])

    def test_with_opensuse_leap_15_x86_64(self) -> None:
        """Testing get_install_steps with openSUSE Leap 15 (x86_64)"""
        install_state = self.create_install_state(
            arch='x86_64',
            distro_id='opensuse-leap',
            distro_families={
                'opensuse',
                'opensuse-leap',
                'suse',
            },
            version='15.5')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'zypper', 'install', '-y', '-t', 'pattern',
                        'devel_basis',
                    ],
                },
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.ZYPPER,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc-c++',
                        'libffi-devel',
                        'libopenssl-devel',
                        'libxml2-devel',
                        'python3-devel',
                        'xmlsec1-devel',
                        'xmlsec1-openssl-devel',
                        'git',
                        'memcached',
                        'libmariadb-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_ARM64_STEPS,
            ])

    def test_with_opensuse_leap_15_aarch64(self) -> None:
        """Testing get_install_steps with openSUSE Leap 15 (aarch64)"""
        install_state = self.create_install_state(
            arch='aarch64',
            distro_id='opensuse-leap',
            distro_families={
                'opensuse',
                'opensuse-leap',
                'suse',
            },
            version='15.5')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'zypper', 'install', '-y', '-t', 'pattern',
                        'devel_basis',
                    ],
                },
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.ZYPPER,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc-c++',
                        'libffi-devel',
                        'libopenssl-devel',
                        'libxml2-devel',
                        'python3-devel',
                        'xmlsec1-devel',
                        'xmlsec1-openssl-devel',
                        'git',
                        'memcached',
                        'libmariadb-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_X86_STEPS,
            ])

    def test_with_opensuse_tumbleweed_x86_64(self) -> None:
        """Testing get_install_steps with openSUSE Tumbleweed (x86_64)"""
        install_state = self.create_install_state(
            arch='x86_64',
            distro_id='opensuse-tumbleweed',
            distro_families={
                'opensuse',
                'opensuse-tumbleweed',
                'suse',
            },
            version='20231215')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'zypper', 'install', '-y', '-t', 'pattern',
                        'devel_basis',
                    ],
                },
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.ZYPPER,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc-c++',
                        'libffi-devel',
                        'libopenssl-devel',
                        'libxml2-devel',
                        'python3-devel',
                        'xmlsec1-devel',
                        'xmlsec1-openssl-devel',
                        'git',
                        'memcached',
                        'libmariadb-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_ARM64_STEPS,
            ])

    def test_with_opensuse_tumbleweed_aarch64(self) -> None:
        """Testing get_install_steps with openSUSE Tumbleweed (aarch64)"""
        install_state = self.create_install_state(
            arch='aarch64',
            distro_id='opensuse-tumbleweed',
            distro_families={
                'opensuse',
                'opensuse-tumbleweed',
                'suse',
            },
            version='20231215')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'zypper', 'install', '-y', '-t', 'pattern',
                        'devel_basis',
                    ],
                },
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.ZYPPER,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc-c++',
                        'libffi-devel',
                        'libopenssl-devel',
                        'libxml2-devel',
                        'python3-devel',
                        'xmlsec1-devel',
                        'xmlsec1-openssl-devel',
                        'git',
                        'memcached',
                        'libmariadb-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_X86_STEPS,
            ])

    def test_with_rhel_8_x86_64(self) -> None:
        """Testing get_install_steps with RHEL 8 (x86_64)"""
        install_state = self.create_install_state(
            arch='x86_64',
            distro_id='rhel',
            distro_families={
                'fedora',
                'rhel',
            },
            version='8.9')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.YUM,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc',
                        'gcc-c++',
                        'libffi-devel',
                        'libxml2-devel',
                        'make',
                        'openssl-devel',
                        'patch',
                        'perl',
                        'python3-devel',
                        'libtool-ltdl-devel',
                        'git',
                        'memcached',
                        'mariadb-connector-c-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_ARM64_STEPS,
            ])

    def test_with_rhel_8_aarch64(self) -> None:
        """Testing get_install_steps with RHEL 8 (aarch64)"""
        install_state = self.create_install_state(
            arch='aarch64',
            distro_id='rhel',
            distro_families={
                'fedora',
                'rhel',
            },
            version='8.9')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.YUM,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc',
                        'gcc-c++',
                        'libffi-devel',
                        'libxml2-devel',
                        'make',
                        'openssl-devel',
                        'patch',
                        'perl',
                        'python3-devel',
                        'libtool-ltdl-devel',
                        'git',
                        'memcached',
                        'mariadb-connector-c-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_X86_STEPS,
            ])

    def test_with_rhel_9_x86_64(self) -> None:
        """Testing get_install_steps with RHEL 9 (x86_64)"""
        install_state = self.create_install_state(
            arch='x86_64',
            distro_id='rhel',
            distro_families={
                'fedora',
                'rhel',
            },
            version='9.3')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'subscription-manager',
                        'repos',
                        '--enable',
                        'codeready-builder-for-rhel-9-x86_64-rpms',
                    ],
                },
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'dnf', 'install', '-y',
                        ('https://dl.fedoraproject.org/pub/epel/'
                         'epel-release-latest-9.noarch.rpm'),
                    ],
                },
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.YUM,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc',
                        'gcc-c++',
                        'libffi-devel',
                        'libxml2-devel',
                        'make',
                        'openssl-devel',
                        'patch',
                        'perl',
                        'python3-devel',
                        'libtool-ltdl-devel',
                        'cvs',
                        'git',
                        'memcached',
                        'mariadb-connector-c-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_ARM64_STEPS,
            ])

    def test_with_rhel_9_aarch64(self) -> None:
        """Testing get_install_steps with RHEL 9 (aarch64)"""
        install_state = self.create_install_state(
            arch='aarch64',
            distro_id='rhel',
            distro_families={
                'fedora',
                'rhel',
            },
            version='9.3')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'subscription-manager',
                        'repos',
                        '--enable',
                        'codeready-builder-for-rhel-9-aarch64-rpms',
                    ],
                },
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'dnf', 'install', '-y',
                        ('https://dl.fedoraproject.org/pub/epel/'
                         'epel-release-latest-9.noarch.rpm'),
                    ],
                },
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.YUM,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc',
                        'gcc-c++',
                        'libffi-devel',
                        'libxml2-devel',
                        'make',
                        'openssl-devel',
                        'patch',
                        'perl',
                        'python3-devel',
                        'libtool-ltdl-devel',
                        'cvs',
                        'git',
                        'memcached',
                        'mariadb-connector-c-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_X86_STEPS,
            ])

    def test_with_rocky_linux_8_x86_64(self) -> None:
        """Testing get_install_steps with Rocky Linux 8 (x86_64)"""
        install_state = self.create_install_state(
            arch='x86_64',
            distro_id='rocky',
            distro_families={
                'centos',
                'fedora',
                'rhel',
                'rocky',
            },
            version='8.9')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'dnf', 'install', '-y', 'dnf-plugins-core',
                    ],
                },
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'yum', 'install', '-y', 'epel-release',
                    ],
                },
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.YUM,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc',
                        'gcc-c++',
                        'libffi-devel',
                        'libxml2-devel',
                        'make',
                        'openssl-devel',
                        'patch',
                        'perl',
                        'python3-devel',
                        'libtool-ltdl-devel',
                        'cvs',
                        'git',
                        'memcached',
                        'mariadb-connector-c-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_ARM64_STEPS,
            ])

    def test_with_rocky_linux_8_aarch64(self) -> None:
        """Testing get_install_steps with Rocky Linux 8 (aarch64)"""
        install_state = self.create_install_state(
            arch='aarch64',
            distro_id='rocky',
            distro_families={
                'centos',
                'fedora',
                'rhel',
                'rocky',
            },
            version='8.9')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'dnf', 'install', '-y', 'dnf-plugins-core',
                    ],
                },
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'yum', 'install', '-y', 'epel-release',
                    ],
                },
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.YUM,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc',
                        'gcc-c++',
                        'libffi-devel',
                        'libxml2-devel',
                        'make',
                        'openssl-devel',
                        'patch',
                        'perl',
                        'python3-devel',
                        'libtool-ltdl-devel',
                        'cvs',
                        'git',
                        'memcached',
                        'mariadb-connector-c-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_X86_STEPS,
            ])

    def test_with_rocky_linux_9_x86_64(self) -> None:
        """Testing get_install_steps with Rocky Linux 9 (x86_64)"""
        install_state = self.create_install_state(
            arch='x86_64',
            distro_id='rocky',
            distro_families={
                'centos',
                'fedora',
                'rhel',
                'rocky',
            },
            version='9.3')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'dnf', 'install', '-y', 'dnf-plugins-core',
                    ],
                },
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'dnf', 'config-manager', '--set-enabled', 'crb',
                    ],
                },
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'yum', 'install', '-y', 'epel-release',
                    ],
                },
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.YUM,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc',
                        'gcc-c++',
                        'libffi-devel',
                        'libxml2-devel',
                        'make',
                        'openssl-devel',
                        'patch',
                        'perl',
                        'python3-devel',
                        'libtool-ltdl-devel',
                        'cvs',
                        'git',
                        'memcached',
                        'mariadb-connector-c-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_ARM64_STEPS,
            ])

    def test_with_rocky_linux_9_aarch64(self) -> None:
        """Testing get_install_steps with Rocky Linux 9 (aarch64)"""
        install_state = self.create_install_state(
            arch='aarch64',
            distro_id='rocky',
            distro_families={
                'centos',
                'fedora',
                'rhel',
                'rocky',
            },
            version='9.3')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'dnf', 'install', '-y', 'dnf-plugins-core',
                    ],
                },
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'dnf', 'config-manager', '--set-enabled', 'crb',
                    ],
                },
                {
                    'install_method': InstallMethodType.SHELL,
                    'name': 'Setting up support for packages',
                    'state': [
                        'yum', 'install', '-y', 'epel-release',
                    ],
                },
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.YUM,
                    'name': 'Installing system packages',
                    'state': [
                        'gcc',
                        'gcc-c++',
                        'libffi-devel',
                        'libxml2-devel',
                        'make',
                        'openssl-devel',
                        'patch',
                        'perl',
                        'python3-devel',
                        'libtool-ltdl-devel',
                        'cvs',
                        'git',
                        'memcached',
                        'mariadb-connector-c-devel',
                        'subversion',
                        'subversion-devel',
                    ],
                },
                *self.COMMON_X86_STEPS,
            ])

    def test_with_ubuntu_18_04_x86_64(self) -> None:
        """Testing get_install_steps with Ubuntu 18.04 (x86_64)"""
        install_state = self.create_install_state(
            arch='x86_64',
            distro_id='ubuntu',
            distro_families={
                'debian',
                'ubuntu',
            },
            version='18.04')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.APT,
                    'name': 'Installing system packages',
                    'state': [
                        'build-essential',
                        'libffi-dev',
                        'libjpeg-dev',
                        'libssl-dev',
                        'libxml2-dev',
                        'libxmlsec1-dev',
                        'libxmlsec1-openssl',
                        'patch',
                        'pkg-config',
                        'python3-dev',
                        'python3-pip',
                        'cvs',
                        'git',
                        'memcached',
                        'libmysqlclient-dev',
                        'subversion',
                        'libsvn-dev',
                    ],
                },
                *self.COMMON_ARM64_STEPS,
            ])

    def test_with_ubuntu_18_04_aarch64(self) -> None:
        """Testing get_install_steps with Ubuntu 18.04 (aarch64)"""
        install_state = self.create_install_state(
            arch='aarch64',
            distro_id='ubuntu',
            distro_families={
                'debian',
                'ubuntu',
            },
            version='18.04')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.APT,
                    'name': 'Installing system packages',
                    'state': [
                        'build-essential',
                        'libffi-dev',
                        'libjpeg-dev',
                        'libssl-dev',
                        'libxml2-dev',
                        'libxmlsec1-dev',
                        'libxmlsec1-openssl',
                        'patch',
                        'pkg-config',
                        'python3-dev',
                        'python3-pip',
                        'cvs',
                        'git',
                        'memcached',
                        'libmysqlclient-dev',
                        'subversion',
                        'libsvn-dev',
                    ],
                },
                *self.COMMON_X86_STEPS,
            ])

    def test_with_ubuntu_20_04_x86_64(self) -> None:
        """Testing get_install_steps with Ubuntu 20.04 (x86_64)"""
        install_state = self.create_install_state(
            arch='x86_64',
            distro_id='ubuntu',
            distro_families={
                'debian',
                'ubuntu',
            },
            version='20.04')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.APT,
                    'name': 'Installing system packages',
                    'state': [
                        'build-essential',
                        'libffi-dev',
                        'libjpeg-dev',
                        'libssl-dev',
                        'libxml2-dev',
                        'libxmlsec1-dev',
                        'libxmlsec1-openssl',
                        'patch',
                        'pkg-config',
                        'python3-dev',
                        'python3-pip',
                        'cvs',
                        'git',
                        'memcached',
                        'libmysqlclient-dev',
                        'subversion',
                        'libsvn-dev',
                    ],
                },
                *self.COMMON_ARM64_STEPS,
            ])

    def test_with_ubuntu_20_04_aarch64(self) -> None:
        """Testing get_install_steps with Ubuntu 20.04 (aarch64)"""
        install_state = self.create_install_state(
            arch='aarch64',
            distro_id='ubuntu',
            distro_families={
                'debian',
                'ubuntu',
            },
            version='20.04')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.APT,
                    'name': 'Installing system packages',
                    'state': [
                        'build-essential',
                        'libffi-dev',
                        'libjpeg-dev',
                        'libssl-dev',
                        'libxml2-dev',
                        'libxmlsec1-dev',
                        'libxmlsec1-openssl',
                        'patch',
                        'pkg-config',
                        'python3-dev',
                        'python3-pip',
                        'cvs',
                        'git',
                        'memcached',
                        'libmysqlclient-dev',
                        'subversion',
                        'libsvn-dev',
                    ],
                },
                *self.COMMON_X86_STEPS,
            ])

    def test_with_ubuntu_22_04_x86_64(self) -> None:
        """Testing get_install_steps with Ubuntu 22.04 (x86_64)"""
        install_state = self.create_install_state(
            arch='x86_64',
            distro_id='ubuntu',
            distro_families={
                'debian',
                'ubuntu',
            },
            version='22.04')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.APT,
                    'name': 'Installing system packages',
                    'state': [
                        'build-essential',
                        'libffi-dev',
                        'libjpeg-dev',
                        'libssl-dev',
                        'libxml2-dev',
                        'libxmlsec1-dev',
                        'libxmlsec1-openssl',
                        'patch',
                        'pkg-config',
                        'python3-dev',
                        'python3-pip',
                        'cvs',
                        'git',
                        'memcached',
                        'libmysqlclient-dev',
                        'subversion',
                        'libsvn-dev',
                    ],
                },
                *self.COMMON_ARM64_STEPS,
            ])

    def test_with_ubuntu_22_04_aarch64(self) -> None:
        """Testing get_install_steps with Ubuntu 22.04 (aarch64)"""
        install_state = self.create_install_state(
            arch='aarch64',
            distro_id='ubuntu',
            distro_families={
                'debian',
                'ubuntu',
            },
            version='22.04')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.APT,
                    'name': 'Installing system packages',
                    'state': [
                        'build-essential',
                        'libffi-dev',
                        'libjpeg-dev',
                        'libssl-dev',
                        'libxml2-dev',
                        'libxmlsec1-dev',
                        'libxmlsec1-openssl',
                        'patch',
                        'pkg-config',
                        'python3-dev',
                        'python3-pip',
                        'cvs',
                        'git',
                        'memcached',
                        'libmysqlclient-dev',
                        'subversion',
                        'libsvn-dev',
                    ],
                },
                *self.COMMON_X86_STEPS,
            ])

    def test_with_ubuntu_23_10_x86_64(self) -> None:
        """Testing get_install_steps with Ubuntu 23.10 (x86_64)"""
        install_state = self.create_install_state(
            arch='x86_64',
            distro_id='ubuntu',
            distro_families={
                'debian',
                'ubuntu',
            },
            version='23.10')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.APT,
                    'name': 'Installing system packages',
                    'state': [
                        'build-essential',
                        'libffi-dev',
                        'libjpeg-dev',
                        'libssl-dev',
                        'libxml2-dev',
                        'libxmlsec1-dev',
                        'libxmlsec1-openssl',
                        'patch',
                        'pkg-config',
                        'python3-dev',
                        'python3-pip',
                        'cvs',
                        'git',
                        'memcached',
                        'libmysqlclient-dev',
                        'subversion',
                        'libsvn-dev',
                    ],
                },
                *self.COMMON_ARM64_STEPS,
            ])

    def test_with_ubuntu_23_10_aarch64(self) -> None:
        """Testing get_install_steps with Ubuntu 23.10 (aarch64)"""
        install_state = self.create_install_state(
            arch='aarch64',
            distro_id='ubuntu',
            distro_families={
                'debian',
                'ubuntu',
            },
            version='23.10')

        self.assertEqual(
            get_install_steps(install_state=install_state),
            [
                {
                    'allow_fail': False,
                    'install_method': InstallMethodType.APT,
                    'name': 'Installing system packages',
                    'state': [
                        'build-essential',
                        'libffi-dev',
                        'libjpeg-dev',
                        'libssl-dev',
                        'libxml2-dev',
                        'libxmlsec1-dev',
                        'libxmlsec1-openssl',
                        'patch',
                        'pkg-config',
                        'python3-dev',
                        'python3-pip',
                        'cvs',
                        'git',
                        'memcached',
                        'libmysqlclient-dev',
                        'subversion',
                        'libsvn-dev',
                    ],
                },
                *self.COMMON_X86_STEPS,
            ])

    def create_install_state(
        self,
        *,
        arch: str = 'x86_64',
        system: str = 'Linux',
        version: str = '',
        distro_id: str = '',
        distro_families: Set[str] = set(),
    ) -> InstallState:
        install_method = get_default_linux_install_method(
            families=distro_families)
        assert install_method

        return {
            'create_sitedir': False,
            'dry_run': False,
            'install_reviewbot_extension': True,
            'install_reviewbot_worker': True,
            'install_powerpack': True,
            'powerpack_version_info': {
                'is_latest': True,
                'is_requested': True,
                'latest_version': '5.2.2',
                'package_name': 'ReviewBoardPowerPack',
                'requires_python': '>=3.7',
                'version': '5.2.2',
            },
            'reviewboard_version_info': {
                'is_latest': True,
                'is_requested': True,
                'latest_version': '6.0',
                'package_name': 'ReviewBoard',
                'requires_python': '>=3.8',
                'version': '6.0',
            },
            'reviewbot_extension_version_info': {
                'is_latest': True,
                'is_requested': True,
                'latest_version': '4.0',
                'package_name': 'reviewbot-extension',
                'requires_python': '>=3.8',
                'version': '4.0',
            },
            'reviewbot_worker_version_info': {
                'is_latest': True,
                'is_requested': True,
                'latest_version': '4.0',
                'package_name': 'reviewbot-worker',
                'requires_python': '>=3.8',
                'version': '4.0',
            },
            'sitedir_path': '/var/www/reviewboard',
            'steps': [],
            'system_info': {
                'arch': arch,
                'bootstrap_python_exe': '/path/to/bootstrap/python',
                'distro_id': distro_id,
                'distro_families': distro_families,
                'paths': {},
                'system_install_method': install_method,
                'system': system,
                'system_python_exe': '/usr/bin/python',
                'system_python_version': (3, 11, 0, '', 0),
                'version': version,
            },
            'unattended_install': False,
            'venv_path': '/path/to/venv',
            'venv_pip_exe': '/path/to/venv/bin/pip',
            'venv_python_exe': '/path/to/venv/bin/python',
        }
