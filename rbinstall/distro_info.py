"""Information on operating systems/distributions and their packages.

Version Added:
    1.0
"""

# NOTE: This file must be syntactically compatible with Python 3.7+.
from __future__ import annotations

import operator
from datetime import date
from typing import Dict, List, Mapping, Set, TYPE_CHECKING

from typing_extensions import Literal, NotRequired, TypeAlias, TypedDict

from rbinstall.install_methods import InstallMethodType
from rbinstall.versioning import VersionMatchFunc, match_version

if TYPE_CHECKING:
    from collections.abc import Sequence


#: Known distro IDs.
#:
#: Version Added:
#:     1.3
DistroID: TypeAlias = Literal[
    'amzn',
    'arch',
    'centos',
    'debian',
    'fedora',
    'opensuse-leap',
    'opensuse-tumbleweed',
    'rhel',
    'rocky',
    'ubuntu',
]


#: Known distro families.
#:
#: Version Added:
#:     1.3
DistroFamily: TypeAlias = Literal[
    'amzn',
    'arch',
    'centos',
    'debian',
    'fedora',
    'opensuse',
    'rhel',
    'rocky',
    'ubuntu',
]


class _PackageCandidateMatch(TypedDict):
    """A match for selecting a candidate package for installation.

    Version Added:
        1.0
    """

    #: Any architectures that must be matched.
    archs: NotRequired[Set[str]]

    #: Any Linux distribution families that must be matched.
    distro_families: NotRequired[Set[DistroFamily]]

    #: Any Linux distribution IDs that must be matched.
    distro_ids: NotRequired[Set[DistroID]]

    #: A callable for determining if a Linux distribution version matches.
    distro_version: NotRequired[VersionMatchFunc]

    #: A set of flags that must be set from previous matched packages.
    has_flags: NotRequired[Dict[str, bool]]

    #: A callable for determining if a Review Board version matches.
    rb_version: NotRequired[VersionMatchFunc]

    #: Any operating systems that must be matched.
    systems: NotRequired[Set[str]]


class _PackageCandidate(TypedDict):
    """A candidate package for installation.

    Version Added:
        1.0
    """

    #: A list of external commands that would be run.
    commands: NotRequired[List[List[str]]]

    #: The installation method used for installing the package.
    #:
    #: If not specified, the system-default installer will be used.
    install_method: NotRequired[InstallMethodType]

    #: Whether this installation step is allowed to fail.
    #:
    #: If allowed to fail, an unsuccessful package installation will not
    #: cause the overall Review Board installation to fail.
    allow_fail: NotRequired[bool]

    #: Any conditions that must be matched for installation.
    match: NotRequired[_PackageCandidateMatch]

    #: A list of packages that would be installed.
    packages: NotRequired[List[str]]

    #: Flags to set for future package matches.
    set_flags: NotRequired[Dict[str, bool]]

    #: A list of packages to skip from prior matched candidates.
    #:
    #: This is used to discard/skip a package that was selected for
    #: installation using this installation method from a previous candidate.
    #: It can be used to specify a corrected package for a more specific
    #: version of an operating system/distribution.
    skip_packages: NotRequired[List[str]]


_PackageTypeDict: TypeAlias = List[_PackageCandidate]
_PackageBundleDict: TypeAlias = Dict[str, _PackageTypeDict]
_Packages: TypeAlias = Dict[str, _PackageBundleDict]


#: All packages available for installation across all supported systems.
#:
#: Version Added:
#:     1.0
PACKAGES: _Packages = {
    # System packages for installation.
    #
    # Some of these (such as xmlsec support) are installed unconditionally,
    # regardless of any selected featuresets, in order to ease usage of those
    # modules down the road.
    'common': {
        'system': [
            #############################################
            # Package management bootstrapping commands #
            #############################################

            # Amazon Linux 2
            {
                'match': {
                    'systems': {'Linux'},
                    'distro_ids': {'amzn'},
                    'distro_version': match_version(2),
                },
                'commands': [
                    [
                        # Needed for g++ and friends.
                        'yum', 'groupinstall', '-y', 'Development Tools',
                    ],
                ],
            },

            # CentOS 9 Stream and below
            {
                'match': {
                    'systems': {'Linux'},
                    'distro_ids': {'centos'},
                    'distro_version': match_version(10, op=operator.lt),
                },
                'commands': [
                    [
                        'dnf', 'install', '-y', 'dnf-plugins-core',
                    ],
                    [
                        'dnf', 'config-manager', '--set-enabled', 'crb',
                    ],
                    [
                        'yum', 'install', '-y', 'epel-release',
                        'epel-next-release',
                    ],
                ],
            },

            # CentOS 10 Stream
            {
                'match': {
                    'systems': {'Linux'},
                    'distro_ids': {'centos'},
                    'distro_version': match_version(10, op=operator.ge),
                },
                'commands': [
                    [
                        'dnf', 'install', '-y', 'dnf-plugins-core',
                    ],
                    [
                        'dnf', 'config-manager', '--set-enabled', 'crb',
                    ],
                    [
                        'yum', 'install', '-y', 'epel-release',
                    ],
                ],
            },

            # openSUSE
            {
                'match': {
                    'systems': {'Linux'},
                    'distro_families': {'opensuse'},
                },
                'commands': [
                    [
                        'zypper', 'install', '-y', '-t', 'pattern',
                        'devel_basis',
                    ],
                ],
            },

            # Red Hat Enterprise Linux 8 (x86)
            {
                'match': {
                    'archs': {'x86_64'},
                    'systems': {'Linux'},
                    'distro_ids': {'rhel'},
                    'distro_version': match_version(8),
                },
                'commands': [
                    [
                        'subscription-manager', 'repos', '--enable',
                        'codeready-builder-for-rhel-8-x86_64-rpms',
                    ],
                    [
                        'dnf', 'install', '-y',
                        ('https://dl.fedoraproject.org/pub/epel/'
                         'epel-release-latest-8.noarch.rpm'),
                    ],
                ],
            },

            # Red Hat Enterprise Linux 8 (ARM)
            {
                'match': {
                    'archs': {'aarch64'},
                    'systems': {'Linux'},
                    'distro_ids': {'rhel'},
                    'distro_version': match_version(8),
                },
                'commands': [
                    [
                        'subscription-manager', 'repos', '--enable',
                        'codeready-builder-for-rhel-8-aarch64-rpms',
                    ],
                    [
                        'dnf', 'install', '-y',
                        ('https://dl.fedoraproject.org/pub/epel/'
                         'epel-release-latest-8.noarch.rpm'),
                    ],
                ],
            },

            # Red Hat Enterprise Linux 9 (x86)
            {
                'match': {
                    'archs': {'x86_64'},
                    'systems': {'Linux'},
                    'distro_ids': {'rhel'},
                    'distro_version': match_version(9),
                },
                'commands': [
                    [
                        'subscription-manager', 'repos', '--enable',
                        'codeready-builder-for-rhel-9-x86_64-rpms',
                    ],
                    [
                        'dnf', 'install', '-y',
                        ('https://dl.fedoraproject.org/pub/epel/'
                         'epel-release-latest-9.noarch.rpm'),
                    ],
                ],
            },

            # Red Hat Enterprise Linux 9 (ARM)
            {
                'match': {
                    'archs': {'aarch64'},
                    'systems': {'Linux'},
                    'distro_ids': {'rhel'},
                    'distro_version': match_version(9),
                },
                'commands': [
                    [
                        'subscription-manager', 'repos', '--enable',
                        'codeready-builder-for-rhel-9-aarch64-rpms',
                    ],
                    [
                        'dnf', 'install', '-y',
                        ('https://dl.fedoraproject.org/pub/epel/'
                         'epel-release-latest-9.noarch.rpm'),
                    ],
                ],
            },

            # Rocky Linux 8
            {
                'match': {
                    'systems': {'Linux'},
                    'distro_ids': {'rocky'},
                    'distro_version': match_version(9, op=operator.lt),
                },
                'commands': [
                    [
                        'dnf', 'install', '-y', 'dnf-plugins-core',
                    ],
                    [
                        'yum', 'install', '-y', 'epel-release',
                    ],
                ],
            },

            # Rocky Linux 9
            {
                'match': {
                    'systems': {'Linux'},
                    'distro_ids': {'rocky'},
                    'distro_version': match_version(9, op=operator.ge),
                },
                'commands': [
                    [
                        'dnf', 'install', '-y', 'dnf-plugins-core',
                    ],
                    [
                        'dnf', 'config-manager', '--set-enabled', 'crb',
                    ],
                    [
                        'yum', 'install', '-y', 'epel-release',
                    ],
                ],
            },

            ############
            # Packages #
            ############

            # Arch Linux
            {
                'match': {
                    'systems': {'Linux'},
                    'distro_ids': {'arch'},
                },
                'install_method': InstallMethodType.PACMAN,
                'packages': [
                    'base-devel',
                    'libffi',
                    'libxml2',
                    'libxslt',
                    'openssl',
                    'perl',
                    'xmlsec',
                ],
                'set_flags': {
                    'has_xmlsec': True,
                },
            },

            # Amazon Linux/CentOS/Fedora/RHEL/Rocky Linux
            {
                # Common rules for all RPM-based distros.
                #
                # More specific rules for given distros will follow, as they
                # don't all share the same packages or naming conventions.
                'match': {
                    'systems': {'Linux'},
                    'distro_families': {
                        'amzn',
                        'centos',
                        'fedora',
                        'rhel',
                    },
                },
                'install_method': InstallMethodType.YUM,
                'packages': [
                    'gcc',
                    'gcc-c++',
                    'libffi-devel',
                    'libxml2-devel',
                    'libxslt-devel',
                    'make',
                    'openssl-devel',
                    'patch',
                    'perl',
                    'python3-devel',
                    'libtool-ltdl-devel',
                ],
            },

            # CentOS 9+
            {
                'match': {
                    'systems': {'Linux'},
                    'distro_ids': {'centos'},
                    'distro_version': match_version(9, op=operator.ge),
                },
                'packages': [
                    'xmlsec1-devel',
                    'xmlsec1-openssl-devel',
                ],
                'set_flags': {
                    'has_xmlsec': True,
                },
            },

            # Fedora
            {
                'match': {
                    'systems': {'Linux'},
                    'distro_ids': {'fedora'},
                },
                'packages': [
                    'xmlsec1-devel',
                    'xmlsec1-openssl-devel',
                ],
                'set_flags': {
                    'has_xmlsec': True,
                },
            },

            # Red Hat Enterprise Linux 9+
            {
                'match': {
                    'systems': {'Linux'},
                    'distro_ids': {'rhel'},
                    'distro_version': match_version(9, op=operator.ge),
                },
                'packages': [
                    'xmlsec1-devel',
                    'xmlsec1-openssl-devel',
                ],
                'set_flags': {
                    'has_xmlsec': True,
                },
            },

            # Rocky Linux 9+
            {
                'match': {
                    'systems': {'Linux'},
                    'distro_ids': {'rocky'},
                    'distro_version': match_version(9, op=operator.ge),
                },
                'packages': [
                    'xmlsec1-devel',
                    'xmlsec1-openssl-devel',
                ],
                'set_flags': {
                    'has_xmlsec': True,
                },
            },

            # Debian/Ubuntu
            {
                'match': {
                    'systems': {'Linux'},
                    'distro_families': {
                        'debian',
                        'ubuntu',
                    },
                },
                'install_method': InstallMethodType.APT,
                'packages': [
                    'build-essential',
                    'libffi-dev',
                    'libjpeg-dev',
                    'libssl-dev',
                    'libxml2-dev',
                    'libxslt-dev',
                    'libxmlsec1-dev',
                    'libxmlsec1-openssl',
                    'patch',
                    'pkg-config',
                    'python3-dev',
                    'python3-pip',
                ],
                'set_flags': {
                    'has_xmlsec': True,
                },
            },

            # openSUSE
            {
                'match': {
                    'systems': {'Linux'},
                    'distro_families': {
                        'opensuse',
                    },
                },
                'install_method': InstallMethodType.ZYPPER,
                'packages': [
                    'gcc-c++',
                    'libffi-devel',
                    'libopenssl-devel',
                    'libxml2-devel',
                    'libxslt-devel',
                    'python3-devel',
                    'xmlsec1-devel',
                    'xmlsec1-openssl-devel',
                ],
                'set_flags': {
                    'has_xmlsec': True,
                },
            },
        ],

        'virtualenv': [
            {
                'install_method': InstallMethodType.PIP,
                'packages': [
                    'pip',
                    'setuptools',
                    'wheel',

                    # This is required for building against local
                    # xmlsec/libxml2, which avoids crashes and other
                    # errors at runtime.
                    '--no-binary',
                    'lxml',
                    'lxml',
                ],
            },
        ],
    },

    # Django Storages support
    'django-storages': {
        'service-integrations': [
            {
                'install_method': InstallMethodType.REVIEWBOARD_EXTRA,
                'packages': [
                    's3',
                    'swift',
                ],
            },
        ],
    },

    # CVS packages.
    'cvs': {
        'system': [
            # Arch Linux
            {
                'match': {
                    'systems': {'Linux'},
                    'distro_ids': {
                        'amzn',
                        'arch',
                        'centos',
                        'debian',
                        'fedora',
                        'opensuse-leap',
                        'opensuse-tumbleweed',
                        'rocky',
                        'ubuntu',
                    },
                },
                'install_method': InstallMethodType.SYSTEM_DEFAULT,
                'packages': ['cvs'],
            },

            # Red Hat Enterprise Linux 9+
            {
                'match': {
                    'systems': {'Linux'},
                    'distro_ids': {'rhel'},
                    'distro_version': match_version(9, op=operator.ge),
                },
                'install_method': InstallMethodType.SYSTEM_DEFAULT,
                'packages': ['cvs'],
            },

            # macOS
            {
                'match': {
                    'systems': {'Darwin'},
                },
                'install_method': InstallMethodType.BREW,
                'packages': ['cvs'],
            },
        ],
    },

    # Git packages.
    'git': {
        'system': [
            {
                'install_method': InstallMethodType.SYSTEM_DEFAULT,
                'packages': ['git'],
            },
        ],
    },

    # LDAP packages.
    'ldap': {
        'service-integrations': [
            {
                'install_method': InstallMethodType.REVIEWBOARD_EXTRA,
                'packages': ['ldap'],
            },
        ],
    },

    # Memcached packages.
    'memcached': {
        'system': [
            # Common
            {
                'match': {
                    'systems': {
                        'Darwin',
                        'Linux',
                    },
                },
                'install_method': InstallMethodType.SYSTEM_DEFAULT,
                'packages': ['memcached'],
            },
        ],
    },

    # Mercurial packages.
    'mercurial': {
        'service-integrations': [
            {
                'install_method': InstallMethodType.REVIEWBOARD_EXTRA,
                'packages': ['mercurial'],
            },
        ],
    },

    # MySQL packages.
    'mysql': {
        'system': [
            # Amazon Linux/CentOS/Fedora/RHEL
            {
                'match': {
                    'systems': {'Linux'},
                    'distro_families': {
                        'centos',
                        'fedora',
                        'rhel',
                        'rocky',
                    },
                },
                'install_method': InstallMethodType.YUM,
                'packages': [
                    'mariadb-connector-c-devel',
                ],
            },

            # Amazon Linux 2
            {
                # This version uses a different package for the MySQL devel
                # support.
                'match': {
                    'systems': {'Linux'},
                    'distro_ids': {'amzn'},
                    'distro_version': match_version(2),
                },
                'install_method': InstallMethodType.YUM,
                'skip_packages': [
                    'mariadb-connector-c-devel',
                ],
                'packages': [
                    'mariadb-devel',
                ],
            },

            # Arch Linux
            {
                'match': {
                    'systems': {'Linux'},
                    'distro_ids': {'arch'},
                },
                'install_method': InstallMethodType.PACMAN,
                'packages': [
                    'mariadb-libs',
                ],
            },

            # Debian
            {
                'match': {
                    'systems': {'Linux'},
                    'distro_ids': {'debian'},
                },
                'install_method': InstallMethodType.APT,
                'packages': [
                    'libmariadb-dev',
                ],
            },

            # openSUSE
            {
                'match': {
                    'systems': {'Linux'},
                    'distro_families': {'opensuse'},
                },
                'install_method': InstallMethodType.ZYPPER,
                'packages': [
                    'libmariadb-devel',
                ],
            },

            # Ubuntu
            {
                'match': {
                    'systems': {'Linux'},
                    'distro_ids': {'ubuntu'},
                },
                'install_method': InstallMethodType.APT,
                'packages': [
                    'libmysqlclient-dev',
                ],
            },

            # macOS
            {
                'match': {
                    'systems': {'Darwin'},
                },
                'install_method': InstallMethodType.BREW,
                'packages': [
                    'mysql',
                ],
            },
        ],

        'service-integrations': [
            {
                'install_method': InstallMethodType.REVIEWBOARD_EXTRA,
                'packages': ['mysql'],
            },
        ],
    },

    # Perforce packages.
    'perforce': {
        'service-integrations': [
            # Linux (Common)
            {
                'allow_fail': True,
                'match': {
                    'archs': {'x86_64'},
                    'systems': {'Linux'},
                },
                'install_method': InstallMethodType.REVIEWBOARD_EXTRA,
                'packages': ['p4'],
            },

            # macOS
            {
                'allow_fail': True,
                'match': {
                    'systems': {'Darwin'},
                },
                'install_method': InstallMethodType.REVIEWBOARD_EXTRA,
                'packages': ['p4'],
            },
        ],
    },

    # Postgres packages.
    'postgres': {
        'service-integrations': [
            {
                # Common
                'install_method': InstallMethodType.REVIEWBOARD_EXTRA,
                'packages': ['postgres']
            },
        ],
    },

    # SAML packages.
    'saml': {
        'service-integrations': [
            {
                'match': {
                    'has_flags': {
                        'has_xmlsec': True,
                    },
                    'rb_version': match_version(6, 0, op=operator.ge),
                },
                'install_method': InstallMethodType.REVIEWBOARD_EXTRA,
                'packages': ['saml'],
            },
        ],
    },

    # Subversion packages.
    'subversion': {
        'system': [
            # Arch Linux
            {
                'match': {
                    'systems': {'Linux'},
                    'distro_ids': {'arch'},
                },
                'install_method': InstallMethodType.PACMAN,
                'packages': [
                    'subversion',
                ],
            },

            # Centos/Fedora/RHEL
            {
                'match': {
                    'systems': {'Linux'},
                    'distro_families': {
                        'centos',
                        'fedora',
                        'rhel',
                    },
                },
                'install_method': InstallMethodType.YUM,
                'packages': [
                    'subversion',
                    'subversion-devel',
                ],
            },

            # Debian/Ubuntu
            {
                'match': {
                    'systems': {'Linux'},
                    'distro_families': {
                        'debian',
                        'ubuntu',
                    },
                },
                'install_method': InstallMethodType.APT,
                'packages': [
                    'subversion',
                    'libsvn-dev',
                ],
            },
            {
                'match': {
                    'systems': {'Linux'},
                    'distro_families': {
                        'debian',
                        'ubuntu',
                    },
                },
                'install_method': InstallMethodType.APT_BUILD_DEP,
                'packages': [
                    'python3-svn',
                ],
            },

            # openSUSE
            {
                'match': {
                    'systems': {'Linux'},
                    'distro_families': {'opensuse'},
                },
                'install_method': InstallMethodType.ZYPPER,
                'packages': [
                    'subversion',
                    'subversion-devel',
                ],
            },

            # macOS
            {
                'match': {
                    'systems': {'Darwin'},
                },
                'install_method': InstallMethodType.BREW,
                'packages': [
                    'subversion',
                ],
            },
        ],

        'service-integrations': [
            # Common
            {
                'install_method': InstallMethodType.REMOTE_PYSCRIPT,
                'packages': [
                    'https://pysvn.reviewboard.org',
                ],
            },
        ],
    },
}


class _DistroInfo(TypedDict):
    """Information about a Linux distribution.

    Version Added:
        1.3
    """

    #: The name of the distro.
    name: str

    #: End-of-life information for various versions.
    #:
    #: This is an *ordered* list of (version match, tuple) entries. To
    #: determine if a given distro version is end of life, this list will be
    #: scanned in order. If the version func matches, the date will be compared
    #: against the current date to make a determination. If there are no
    #: matches, the version will be assumed to be currently maintained.
    eol: Sequence[tuple[VersionMatchFunc, date]]


_DistroInfos: TypeAlias = Mapping[str, _DistroInfo]


#: Information about known Linux distributions.
#:
#: Version Added:
#:    1.3
DISTROS: _DistroInfos = {
    'amzn': {
        'name': 'Amazon Linux',
        'eol': [
            (match_version(2, op=operator.le), date(2026, 6, 30)),
            (match_version(2023), date(2029, 6, 30)),
        ],
    },
    'arch': {
        'name': 'Arch Linux',
        'eol': [
            # Arch is evergreen.
        ],
    },
    'centos': {
        'name': 'CentOS',
        'eol': [
            (match_version(8, op=operator.le), date(2024, 5, 31)),
            (match_version(9), date(2027, 5, 31)),
            (match_version(10), date(2030, 1, 1)),
        ],
    },
    'debian': {
        'name': 'Debian',
        'eol': [
            (match_version(10, op=operator.le), date(2022, 9, 10)),
            (match_version(11), date(2024, 8, 14)),
            (match_version(12), date(2026, 6, 10)),
            (match_version(13), date(2028, 8, 9)),
        ],
    },
    'fedora': {
        'name': 'Fedora Linux',
        'eol': [
            (match_version(41, op=operator.le), date(2025, 12, 15)),
            (match_version(42), date(2026, 5, 13)),
            (match_version(43), date(2026, 12, 9)),
        ],
    },
    'opensuse-leap': {
        'name': 'openSUSE Leap',
        'eol': [
            # openSUSE Leap 14 was mistakenly labeled version 42.
            (match_version(42), date(2019, 7, 1)),

            # openSUSE Leap 15 has a bunch of older versions that we don't
            # care to list individually.
            (match_version(15, 5, op=operator.le), date(2024, 12, 31)),
            (match_version(15, 6), date(2026, 4, 30)),
            (match_version(16), date(2027, 10, 31)),
        ],
    },
    'opensuse-tumbleweed': {
        'name': 'openSUSE Tumbleweed',
        'eol': [
            # Tumbleweed is evergreen.
        ],
    },
    'rhel': {
        'name': 'Red Hat Enterprise Linux',
        'eol': [
            (match_version(8, op=operator.le), date(2029, 5, 31)),
            (match_version(9), date(2032, 5, 31)),
            (match_version(10), date(2035, 5, 31)),
        ],
    },
    'rocky': {
        'name': 'Rocky Linux',
        'eol': [
            (match_version(8, op=operator.le), date(2029, 5, 31)),
            (match_version(9), date(2032, 5, 31)),
            (match_version(10), date(2035, 5, 31)),
        ],
    },
    'ubuntu': {
        'name': 'Ubuntu',
        'eol': [
            # LTS releases. These must come first.
            (match_version(18, 4, op=operator.le), date(2023, 5, 31)),
            (match_version(20, 4), date(2025, 5, 31)),
            (match_version(22, 4), date(2027, 4, 1)),
            (match_version(24, 4), date(2029, 5, 31)),

            # Non-LTS releases. The most recent one is listed first, and then
            # the last entry here should catch everything older.
            (match_version(25, 10), date(2026, 6, 1)),
            (match_version(25, 4, op=operator.le), date(2026, 1, 17)),
        ],
    },
}
