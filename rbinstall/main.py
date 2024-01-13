"""Main entry point for the Review Board installer.

Version Added:
    1.0
"""

# NOTE: This file must be syntactically compatible with Python 3.7+.
from __future__ import annotations

import os
import sys

from rbinstall.errors import InstallerError
from rbinstall.install_methods import run_install_method
from rbinstall.install_steps import get_install_steps
from rbinstall.process import die
from rbinstall.pypi import get_package_version_info
from rbinstall.state import InstallState, get_system_info


def main() -> None:
    """Main entry point for the Review Board installer.

    This begins the install process, checking for user preferences and system
    settings and performing the installation process.
    """
    venv_path = '/opt/reviewboard'

    install_state: InstallState = {
        'install_powerpack': True,
        'install_rb_version': '',
        'install_reviewbot_extension': True,
        'install_reviewbot_worker': True,
        'system_info': get_system_info(),
        'venv_path': venv_path,
        'venv_pip_exe': os.path.join(venv_path, 'bin', 'pip'),
        'venv_python_exe': os.path.join(venv_path, 'bin', 'python'),
    }
    system_info = install_state['system_info']

    rb_version_info = get_package_version_info(
        system_info=system_info,
        package_name='ReviewBoard',
        target_version='latest')
    assert rb_version_info, 'Could not find latest Review Board version.'

    install_state['install_rb_version'] = rb_version_info['version']

    print()
    install_steps = get_install_steps(install_state=install_state)

    print()

    for install_step in install_steps:
        print()
        print(install_step['name'])

        try:
            run_install_method(install_method=install_step['install_method'],
                               install_state=install_state,
                               args=install_step.get('state', []))
        except InstallerError as e:
            if install_step.get('allow_fail'):
                sys.stderr.write('%s\n' % e)
                sys.stderr.write('Continuing...\n')
            else:
                die(str(e))


if __name__ == '__main__':
    main()
