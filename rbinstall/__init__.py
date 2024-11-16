"""Review Board Installer version and package information.

These variables and functions can be used to identify the version of the
Review Board Installer. They're largely used for packaging purposes.
"""

#: The version of the Review Board installer.
#:
#: This is in the format of:
#:
#: (Major, Minor, Micro, Patch, alpha/beta/rc/final, Release Number, Released)
#:
VERSION = (1, 2, 1, 0, 'final', 0, True)


def get_version_string() -> str:
    """Return the version as a human-readable string.

    Returns:
        str:
        The installer version.
    """
    major, minor, micro, patch, tag, relnum, is_release = VERSION

    version = f'{major}.{minor}'

    if micro or patch:
        version = f'{version}.{micro}'

        if patch:
            version = f'{version}.{patch}'

    if tag != 'final':
        if tag == 'rc':
            version = f'{version} RC{relnum}'
        else:
            version = f'{version} {tag} {relnum}'

    if not is_release:
        version = f'{version} (dev)'

    return version


def get_package_version() -> str:
    """Return the version as a Python package version string.

    Returns:
        str:
        The version number as used in a Python package.
    """
    major, minor, micro, patch, tag, relnum = __version_info__

    version = f'{major}.{minor}'

    if micro or patch:
        version = f'{version}.{micro}'

        if patch:
            version = f'{version}.{patch}'

    if tag != 'final':
        norm_tag = {
            'alpha': 'a',
            'beta': 'b',
        }.get(tag, tag)
        version = f'{version}{norm_tag}{relnum}'

    return version


def is_release() -> bool:
    """Return whether this is a released version.

    Returns:
        bool:
        ``True`` if this is a released version of the package.
        ``False`` if it is a development version.
    """
    return VERSION[-1]


__version_info__ = VERSION[:-1]
__version__ = get_package_version()
