"""Installation methods for operating systems and distros.

Version Added:
    1.0
"""

# NOTE: This file must be syntactically compatible with Python 3.7+.
from __future__ import annotations

from enum import Enum


class InstallMethodType(str, Enum):
    """Types of installation methods on operating systems and distros.

    Version Added:
        1.0
    """

    #: The Debian/Ubuntu apt/apt-get package manager.
    APT = 'apt'

    #: The Debian/Ubuntu apt-get build-dep command.
    APT_BUILD_DEP = 'apt-build-dep'

    #: The macOS brew package manager.
    BREW = 'brew'

    #: The Arch Linux pacman package manager.
    PACMAN = 'pacman'

    #: The standard pip Python package manager.
    PIP = 'pip'

    #: Download and execution of an online Python script.
    REMOTE_PYSCRIPT = 'remote-pyscript'

    #: Extra package installation targets for Review Board.
    REVIEWBOARD_EXTRA = 'reviewboard-extra'

    #: A shell command.
    SHELL = 'shell'

    #: The RedHat/CentOS/Fedora/etc. "yum" package manager.
    YUM = 'yum'

    #: The OpenSuSE zypper package manager.
    ZYPPER = 'zypper'

    #: An indicator of the default system package tool for a target system.
    SYSTEM_DEFAULT = 'system-default'
