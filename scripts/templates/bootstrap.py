#!/usr/bin/env python3
#
# NOTE: This file must be syntactically-compatible with Python 3.6.
#
# First we'll safeguard against running this as a bash script.
''':'
echo This cannot be run as a shell script. Please run this with the >&2
echo version of Python that you want to use with Review Board. For example: >&2
echo >&2
echo 'curl https://install.reviewboard.org | python3.11' >&2
exit 1
#'''

import atexit
import base64
import os
import shutil
import subprocess
import sys
import tempfile
import venv


def main():
    if sys.version_info < (3, 7):
        sys.stderr.write(
            'The Review Board installer requires Python 3.7 or higher.\n'
            '\n'
            'You may need to upgrade your Linux distribution, install in '
            'a virtual machine\n'
            'or container, or install a newer version of Python.\n'
            '\n'
            'Please see the Review Board documentation for guidance:\n'
            '\n'
            'https://www.reviewboard.org/docs/manual/latest/admin/'
            'installation/rbinstall/\n'
        )
        sys.exit(1)

    stdin_fd = sys.stdin

    if not sys.stdin.isatty():
        # This script was passed to Python. We'll need to reopen this as
        # /dev/tty.
        try:
            stdin_fd = open('/dev/tty', 'r')
        except Exception:
            sys.stderr.write(
                'Warning: Unable to read from /dev/tty. This may prevent\n'
                'you from providing input to the installer. You may want\n'
                'to download this installer and run it manually as a\n'
                'Python script:\n'
                '\n'
                '    $ curl -o rbinstall.py https://install.reviewboard.org\n'
                '    $ %s ./rbinstall.py\n'
                '\n'
                % sys.executable)

    tmp_path = tempfile.mkdtemp(prefix='rbinstall-')
    atexit.register(lambda: shutil.rmtree(tmp_path))

    venv_path = os.path.join(tmp_path, 'venv')
    rbinstall_path = os.path.join(tmp_path, rbinstall_whl_filename)
    python_path = os.path.join(venv_path, 'bin', 'python')

    print('Preparing the Review Board installer... ',
          end='',
          flush=True)
    venv.create(venv_path, with_pip=True)

    with open(rbinstall_path, 'wb') as fp:
        fp.write(base64.b64decode(get_installer_data()))

    subprocess.run(
        [python_path, '-m', 'pip', 'install', '-q', rbinstall_path],
        check=True)

    print('done')
    print()

    # TODO: Env-based args? RBINSTALL_EXPERT or stuff?
    try:
        subprocess.run(
            [
                os.path.join(venv_path, 'bin', 'rbinstall'),
            ] + sys.argv[1:],
            env=dict(
                os.environ,
                RBINSTALL_FORCE_SYSTEM_PYTHON_EXE=sys.executable,
            ),
            stdin=stdin_fd,
            check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
