"""Unit tests for rbinstall.install_methods.

Version Added:
    1.0
"""

from __future__ import annotations

import re
from io import BytesIO
from unittest import TestCase
from urllib.request import urlopen

import kgb

from rbinstall.errors import InstallPackageError, RunCommandError
from rbinstall.install_methods import InstallMethodType, run_install_method
from rbinstall.process import run
from rbinstall.state import InstallState


class RunInstallMethodTests(kgb.SpyAgency, TestCase):
    """Unit tests for run_install_method().

    Version Added:
        1.0
    """

    INSTALL_STATE: InstallState = {
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
            'arch': 'amd64',
            'bootstrap_python_exe': '/path/to/bootstrap/python',
            'paths': {},
            'system_install_method': InstallMethodType.APT,
            'system': 'Linux',
            'system_python_exe': '/usr/bin/python',
            'system_python_version': (3, 11, 0, '', 0),
            'version': '1.2.3',
        },
        'unattended_install': False,
        'venv_path': '/path/to/venv',
        'venv_pip_exe': '/path/to/venv/bin/pip',
        'venv_python_exe': '/path/to/venv/bin/python',
    }

    def test_with_apt(self) -> None:
        """Testing run_install_method with APT"""
        self.spy_on(run, call_original=False)

        run_install_method(install_state=self.INSTALL_STATE,
                           install_method=InstallMethodType.APT,
                           args=['package1', 'package2'])

        self.assertSpyCalledWith(
            run,
            ['apt-get', 'install', '-y', 'package1', 'package2'])

    def test_with_apt_and_error(self) -> None:
        """Testing run_install_method with APT and error"""
        @self.spy_for(run)
        def _run(command, **kwargs):
            raise RunCommandError(command=command,
                                  exit_code=1)

        message = re.escape(
            'There was an error installing one or more packages (package1 '
            'package2). The command that failed was: `apt-get install -y '
            'package1 package2`. The error was: Error executing `apt-get '
            'install -y package1 package2`: exit code 1'
        )

        with self.assertRaisesRegex(InstallPackageError, message) as ctx:
            run_install_method(install_state=self.INSTALL_STATE,
                               install_method=InstallMethodType.APT,
                               args=['package1', 'package2'])

        e = ctx.exception
        self.assertEqual(e.install_method, InstallMethodType.APT)
        self.assertEqual(e.install_state, self.INSTALL_STATE)
        self.assertEqual(e.packages, ['package1', 'package2'])

    def test_with_apt_build_dep(self) -> None:
        """Testing run_install_method with APT_BUILD_DEP"""
        self.spy_on(run, call_original=False)

        run_install_method(install_state=self.INSTALL_STATE,
                           install_method=InstallMethodType.APT_BUILD_DEP,
                           args=['package1', 'package2'])

        self.assertSpyCalledWith(
            run,
            ['apt-get', 'build-dep', '-y', 'package1', 'package2'])

    def test_with_apt_build_dep_and_error(self) -> None:
        """Testing run_install_method with APT_BUILD_DEP and error"""
        @self.spy_for(run)
        def _run(command, **kwargs):
            raise RunCommandError(command=command,
                                  exit_code=1)

        message = re.escape(
            'There was an error installing one or more packages (package1 '
            'package2). The command that failed was: `apt-get build-dep -y '
            'package1 package2`. The error was: Error executing `apt-get '
            'build-dep -y package1 package2`: exit code 1'
        )

        with self.assertRaisesRegex(InstallPackageError, message) as ctx:
            run_install_method(install_state=self.INSTALL_STATE,
                               install_method=InstallMethodType.APT_BUILD_DEP,
                               args=['package1', 'package2'])

        e = ctx.exception
        self.assertEqual(e.install_method, InstallMethodType.APT_BUILD_DEP)
        self.assertEqual(e.install_state, self.INSTALL_STATE)
        self.assertEqual(e.packages, ['package1', 'package2'])

    def test_with_brew(self) -> None:
        """Testing run_install_method with BREW"""
        self.spy_on(run, call_original=False)

        run_install_method(install_state=self.INSTALL_STATE,
                           install_method=InstallMethodType.BREW,
                           args=['package1', 'package2'])

        self.assertSpyCalledWith(
            run,
            ['brew', 'install', 'package1', 'package2'])

    def test_with_brew_and_error(self) -> None:
        """Testing run_install_method with BREW and error"""
        @self.spy_for(run)
        def _run(command, **kwargs):
            raise RunCommandError(command=command,
                                  exit_code=1)

        message = re.escape(
            'There was an error installing one or more packages (package1 '
            'package2). The command that failed was: `brew install package1 '
            'package2`. The error was: Error executing `brew install '
            'package1 package2`: exit code 1'
        )

        with self.assertRaisesRegex(InstallPackageError, message) as ctx:
            run_install_method(install_state=self.INSTALL_STATE,
                               install_method=InstallMethodType.BREW,
                               args=['package1', 'package2'])

        e = ctx.exception
        self.assertEqual(e.install_method, InstallMethodType.BREW)
        self.assertEqual(e.install_state, self.INSTALL_STATE)
        self.assertEqual(e.packages, ['package1', 'package2'])

    def test_with_pacman(self) -> None:
        """Testing run_install_method with PACMAN"""
        self.spy_on(run, call_original=False)

        run_install_method(install_state=self.INSTALL_STATE,
                           install_method=InstallMethodType.PACMAN,
                           args=['package1', 'package2'])

        self.assertSpyCalledWith(
            run,
            ['pacman', '-S', '--noconfirm', 'package1', 'package2'])

    def test_with_pacman_and_error(self) -> None:
        """Testing run_install_method with PACMAN and error"""
        @self.spy_for(run)
        def _run(command, **kwargs):
            raise RunCommandError(command=command,
                                  exit_code=1)

        message = re.escape(
            'There was an error installing one or more packages (package1 '
            'package2). The command that failed was: `pacman -S --noconfirm '
            'package1 package2`. The error was: Error executing `pacman -S '
            '--noconfirm package1 package2`: exit code 1'
        )

        with self.assertRaisesRegex(InstallPackageError, message) as ctx:
            run_install_method(install_state=self.INSTALL_STATE,
                               install_method=InstallMethodType.PACMAN,
                               args=['package1', 'package2'])

        e = ctx.exception
        self.assertEqual(e.install_method, InstallMethodType.PACMAN)
        self.assertEqual(e.install_state, self.INSTALL_STATE)
        self.assertEqual(e.packages, ['package1', 'package2'])

    def test_with_pip(self) -> None:
        """Testing run_install_method with PIP"""
        self.spy_on(run, call_original=False)

        run_install_method(install_state=self.INSTALL_STATE,
                           install_method=InstallMethodType.PIP,
                           args=['package1', 'package2'])

        self.assertSpyCalledWith(
            run,
            [
                '/path/to/venv/bin/pip', 'install',
                '--disable-pip-version-check',
                '--no-python-version-warning',
                'package1', 'package2',
            ])

    def test_with_pip_and_error(self) -> None:
        """Testing run_install_method with PIP and error"""
        @self.spy_for(run)
        def _run(command, **kwargs):
            raise RunCommandError(command=command,
                                  exit_code=1)

        message = re.escape(
            'There was an error installing one or more packages (package1 '
            'package2). The command that failed was: `/path/to/venv/bin/pip '
            'install --disable-pip-version-check --no-python-version-warning '
            'package1 package2`. The error was: Error executing '
            '`/path/to/venv/bin/pip install --disable-pip-version-check '
            '--no-python-version-warning package1 package2`: exit code 1'
        )

        with self.assertRaisesRegex(InstallPackageError, message) as ctx:
            run_install_method(install_state=self.INSTALL_STATE,
                               install_method=InstallMethodType.PIP,
                               args=['package1', 'package2'])

        e = ctx.exception
        self.assertEqual(e.install_method, InstallMethodType.PIP)
        self.assertEqual(e.install_state, self.INSTALL_STATE)
        self.assertEqual(e.packages, ['package1', 'package2'])

    def test_with_remote_pyscript(self) -> None:
        """Testing run_install_method with REMOTE_PYSCRIPT"""
        self.spy_on(run, call_original=False)
        self.spy_on(
            urlopen,
            op=kgb.SpyOpReturn(BytesIO(
                b'import sys\n'
                b'sys.exit(0)\n'
            )))

        run_install_method(install_state=self.INSTALL_STATE,
                           install_method=InstallMethodType.REMOTE_PYSCRIPT,
                           args=['https://install.example.com'])

        self.assertSpyCalled(urlopen)
        self.assertSpyCalled(run)

    def test_with_remote_pyscript_and_error(self) -> None:
        """Testing run_install_method with REMOTE_PYSCRIPT and error"""
        @self.spy_for(run)
        def _run(command, **kwargs):
            raise RunCommandError(command=command,
                                  exit_code=1)

        self.spy_on(
            urlopen,
            op=kgb.SpyOpReturn(BytesIO(
                b'import sys\n'
                b'sys.exit(1)\n'
            )))

        message = (
            r'There was an error installing one or more packages '
            r'\(https://install\.example\.com\). The command that failed was: '
            r'`/path/to/venv/bin/python .+`. The error was: Error executing '
            r'`/path/to/venv/bin/python .*`: exit code 1'
        )

        with self.assertRaisesRegex(InstallPackageError, message) as ctx:
            run_install_method(
                install_state=self.INSTALL_STATE,
                install_method=InstallMethodType.REMOTE_PYSCRIPT,
                args=['https://install.example.com'])

        self.assertSpyCalled(urlopen)
        self.assertSpyCalled(run)

        e = ctx.exception
        self.assertEqual(e.install_method, InstallMethodType.REMOTE_PYSCRIPT)
        self.assertEqual(e.install_state, self.INSTALL_STATE)
        self.assertEqual(e.packages, ['https://install.example.com'])

    def test_with_reviewboard_extra(self) -> None:
        """Testing run_install_method with REVIEWBOARD_EXTRA"""
        self.spy_on(run, call_original=False)

        run_install_method(install_state=self.INSTALL_STATE,
                           install_method=InstallMethodType.REVIEWBOARD_EXTRA,
                           args=['package1', 'package2'])

        self.assertSpyCalledWith(
            run,
            [
                '/path/to/venv/bin/pip', 'install',
                '--disable-pip-version-check',
                '--no-python-version-warning',
                'ReviewBoard[package1]', 'ReviewBoard[package2]',
            ])

    def test_with_reviewboard_extra_and_error(self) -> None:
        """Testing run_install_method with REVIEWBOARD_EXTRA and error"""
        @self.spy_for(run)
        def _run(command, **kwargs):
            raise RunCommandError(command=command,
                                  exit_code=1)

        message = re.escape(
            'There was an error installing one or more packages '
            '(ReviewBoard[package1] ReviewBoard[package2]). The command that '
            'failed was: `/path/to/venv/bin/pip install '
            '--disable-pip-version-check --no-python-version-warning '
            'ReviewBoard[package1] ReviewBoard[package2]`. The error was: '
            'Error executing `/path/to/venv/bin/pip install '
            '--disable-pip-version-check --no-python-version-warning '
            'ReviewBoard[package1] ReviewBoard[package2]`: exit code 1'
        )

        with self.assertRaisesRegex(InstallPackageError, message) as ctx:
            run_install_method(
                install_state=self.INSTALL_STATE,
                install_method=InstallMethodType.REVIEWBOARD_EXTRA,
                args=['package1', 'package2'])

        e = ctx.exception
        self.assertEqual(e.install_method, InstallMethodType.REVIEWBOARD_EXTRA)
        self.assertEqual(e.install_state, self.INSTALL_STATE)
        self.assertEqual(e.packages,
                         ['ReviewBoard[package1]', 'ReviewBoard[package2]'])

    def test_with_shell(self) -> None:
        """Testing run_install_method with SHELL"""
        self.spy_on(run, call_original=False)

        run_install_method(install_state=self.INSTALL_STATE,
                           install_method=InstallMethodType.SHELL,
                           args=['some-command', '--arg1', '--arg2'])

        self.assertSpyCalledWith(
            run,
            [
                'some-command',
                '--arg1',
                '--arg2',
            ])

    def test_with_shell_and_error(self) -> None:
        """Testing run_install_method with SHELL and error"""
        @self.spy_for(run)
        def _run(command, **kwargs):
            raise RunCommandError(command=command,
                                  exit_code=1)

        message = re.escape(
            'There was an error executing the command `some-command --arg1 '
            '--arg2`. The error was: Error executing `some-command --arg1 '
            '--arg2`: exit code 1'
        )

        with self.assertRaisesRegex(InstallPackageError, message) as ctx:
            run_install_method(
                install_state=self.INSTALL_STATE,
                install_method=InstallMethodType.SHELL,
                args=['some-command', '--arg1', '--arg2'])

        e = ctx.exception
        self.assertEqual(e.install_method, InstallMethodType.SHELL)
        self.assertEqual(e.install_state, self.INSTALL_STATE)
        self.assertEqual(e.packages, [])

    def test_with_yum(self) -> None:
        """Testing run_install_method with YUM"""
        self.spy_on(run, call_original=False)

        run_install_method(install_state=self.INSTALL_STATE,
                           install_method=InstallMethodType.YUM,
                           args=['package1', 'package2'])

        self.assertSpyCalledWith(
            run,
            ['yum', 'install', '-y', 'package1', 'package2'])

    def test_with_yum_and_error(self) -> None:
        """Testing run_install_method with YUM and error"""
        @self.spy_for(run)
        def _run(command, **kwargs):
            raise RunCommandError(command=command,
                                  exit_code=1)

        message = re.escape(
            'There was an error installing one or more packages (package1 '
            'package2). The command that failed was: `yum install -y '
            'package1 package2`. The error was: Error executing '
            '`yum install -y package1 package2`: exit code 1'
        )

        with self.assertRaisesRegex(InstallPackageError, message) as ctx:
            run_install_method(install_state=self.INSTALL_STATE,
                               install_method=InstallMethodType.YUM,
                               args=['package1', 'package2'])

        e = ctx.exception
        self.assertEqual(e.install_method, InstallMethodType.YUM)
        self.assertEqual(e.install_state, self.INSTALL_STATE)
        self.assertEqual(e.packages, ['package1', 'package2'])

    def test_with_zypper(self) -> None:
        """Testing run_install_method with ZYPPER"""
        self.spy_on(run, call_original=False)

        run_install_method(install_state=self.INSTALL_STATE,
                           install_method=InstallMethodType.ZYPPER,
                           args=['package1', 'package2'])

        self.assertSpyCalledWith(
            run,
            ['zypper', 'install', '-y', 'package1', 'package2'])

    def test_with_zypper_and_error(self) -> None:
        """Testing run_install_method with ZYPPER and error"""
        @self.spy_for(run)
        def _run(command, **kwargs):
            raise RunCommandError(command=command,
                                  exit_code=1)

        message = re.escape(
            'There was an error installing one or more packages (package1 '
            'package2). The command that failed was: `zypper install -y '
            'package1 package2`. The error was: Error executing '
            '`zypper install -y package1 package2`: exit code 1'
        )

        with self.assertRaisesRegex(InstallPackageError, message) as ctx:
            run_install_method(install_state=self.INSTALL_STATE,
                               install_method=InstallMethodType.ZYPPER,
                               args=['package1', 'package2'])

        e = ctx.exception
        self.assertEqual(e.install_method, InstallMethodType.ZYPPER)
        self.assertEqual(e.install_state, self.INSTALL_STATE)
        self.assertEqual(e.packages, ['package1', 'package2'])
