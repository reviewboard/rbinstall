#!/usr/bin/env python3
"""Test manager for rbinstall Docker images.

This will create Docker images for supported Linux distributions, testing
that rbinstall can successfully install Review Board and create a working
environment.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from configparser import ConfigParser
from dataclasses import dataclass
from enum import Enum
from itertools import chain
from typing import Any, Dict, Iterator, List, Optional
from urllib.parse import urlparse


if sys.stdout.isatty():
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    RESET = '\033[0m'
else:
    GREEN = ''
    RED = ''
    YELLOW = ''
    RESET = ''


# Set up the centralized configuration.
config_filename = os.path.abspath(os.path.join(__file__, '..',
                                               'rbinstall-test.ini'))
config = ConfigParser()

if os.path.exists(config_filename):
    config.read(config_filename)


# Per-package manager common setup.
squid_url = config.get('squid-cache', 'url')
pypi_url = config.get('pypi-cache', 'url')
common_setup_lines: List[str] = []
package_manager_setup_lines: Dict[str, List[str]] = {}

if pypi_url:
    pypi_hostname = urlparse(pypi_url).hostname

    common_setup_lines += [
        f'ENV PIP_TRUSTED_HOST={pypi_hostname}',
        f'ENV PIP_INDEX_URL={pypi_url}',
    ]

if squid_url:
    squid_hostname = urlparse(squid_url).hostname

    common_setup_lines += [
        f'ENV http_proxy={squid_url}',
        f'ENV https_proxy={squid_url}',
        f'ENV no_proxy={squid_hostname}',
    ]
    package_manager_setup_lines['apt'] = [
        f'RUN echo \'Acquire::HTTP::Proxy "{squid_url}";\' >>'
        f' /etc/apt/apt.conf.d/01proxy \\'
        f' && echo \'Acquire::HTTPS::Proxy "false";\''
        f' >> /etc/apt/apt.conf.d/01proxy',
    ]
    package_manager_setup_lines['yum'] = [
        f'RUN echo "proxy={squid_url}" >> /etc/yum.conf',
        f'RUN echo "proxy={squid_url}" >> /etc/dnf/dnf.conf || exit 0',
        'RUN rm -f /etc/yum/pluginconf.d/fastestmirror.conf',
    ]


# Common Linux distribution types.
DIST_TYPES = {
    'amazonlinux': {
        'package_type': 'yum',
        'setup_lines': [
            'ENV container docker',
            'RUN yum update -y && yum install -y python3',
        ],
    },
    'archlinux': {
        'package_type': 'pacman',
        'setup_lines': [
            'RUN pacman --help',
            'RUN pacman -Syu --noconfirm && pacman -S --noconfirm python',
        ],
    },
    'centos': {
        'package_type': 'yum',
        'setup_lines': [
            'ENV container docker',
            'RUN yum update -y && yum install -y python3',
        ],
    },
    'debian': {
        'package_type': 'apt',
        'setup_lines': [
            'ENV TERM=dumb',
            'ENV DEBIAN_FRONTEND=noninteractive',
            'RUN apt-get update -y && apt-get install -y python3 python3-venv',
        ],
    },
    'fedora': {
        'package_type': 'yum',
        'setup_lines': [
            'ENV container docker',
            'RUN yum update -y && yum install -y python3',
        ],
    },
    'opensuse': {
        'package_type': 'zypper',
        'setup_lines': [
            'RUN zypper install -y python3',
        ],
    },
    'rockylinux': {
        'package_type': 'yum',
        'setup_lines': [
            'ENV container docker',
            'RUN yum update -y && yum install -y python3',
        ],
    },
    'ubuntu': {
        'package_type': 'apt',
        'setup_lines': [
            'ENV TERM=dumb',
            'ENV DEBIAN_FRONTEND=noninteractive',
            'RUN apt-get update -y && apt-get install -y python3 python3-venv',
        ],
    },
}

if 'rhel' in config:
    rhel_config = config['rhel']

    DIST_TYPES.update({
        'rhel': {
            'package_type': 'yum',
            'setup_lines': [
                'ENV container docker',

                'RUN subscription-manager register --org=%s'
                ' --activationkey=%s'
                % (rhel_config['organization_id'],
                   rhel_config['activation_key']),

                'RUN yum update -y && yum install -y python3',

                'RUN subscription-manager repos --list',
            ],
        },
    })


# The list of Linux distributions to test.
DISTS = {
    # Amazon Linux
    'amazonlinux:2': {
        'type': 'amazonlinux',
        'image': 'amazonlinux:2',
        'platforms': ['linux/amd64', 'linux/arm64'],
        'python_exe': 'python3.8',
        'setup_lines': [
            'RUN amazon-linux-extras install -y python3.8',
            'RUN yum install -y python38-devel',
        ],
    },
    'amazonlinux:2023': {
        'type': 'amazonlinux',
        'image': 'amazonlinux:2023',
        'platforms': ['linux/amd64', 'linux/arm64'],
    },

    # Arch Linux
    'archlinux:latest': {
        'type': 'archlinux',
        'image': 'archlinux:latest',
        'platforms': ['linux/amd64'],
    },

    # CentOS Stream
    'centos:8': {
        'type': 'centos',
        'image': 'centos:8',
        'platforms': ['linux/amd64'],
        'expect_success': False,
    },
    'centos:stream8': {
        'type': 'centos',
        'image': 'tgagor/centos:stream8',
        'platforms': ['linux/amd64'],
        'expect_success': False,
    },
    'centos:stream9': {
        'type': 'centos',
        'image': 'tgagor/centos:stream9',
        'platforms': ['linux/amd64'],
    },
    'centos:latest': {
        'type': 'centos',
        'image': 'tgagor/centos:latest',
        'platforms': ['linux/amd64'],
    },

    # Debian Linux
    'debian:10': {
        'type': 'debian',
        'image': 'debian:buster',
        'platforms': ['linux/amd64', 'linux/arm64'],
    },
    'debian:11': {
        'type': 'debian',
        'image': 'debian:bullseye',
        'platforms': ['linux/amd64', 'linux/arm64'],
    },
    'debian:12': {
        'type': 'debian',
        'image': 'debian:bookworm',
        'platforms': ['linux/amd64', 'linux/arm64'],
    },
    'debian:latest': {
        'type': 'debian',
        'image': 'debian:latest',
        'platforms': ['linux/amd64', 'linux/arm64'],
    },
    'debian:unstable': {
        'type': 'debian',
        'image': 'debian:unstable',
        'platforms': ['linux/amd64', 'linux/arm64'],
    },
    'debian:stable': {
        'type': 'debian',
        'image': 'debian:stable',
        'platforms': ['linux/amd64', 'linux/arm64'],
    },
    'debian:testing': {
        'type': 'debian',
        'image': 'debian:testing',
        'platforms': ['linux/amd64', 'linux/arm64'],
    },

    # Fedora
    'fedora:36': {
        'type': 'fedora',
        'image': 'fedora:36',
        'platforms': ['linux/amd64', 'linux/arm64'],
    },
    'fedora:37': {
        'type': 'fedora',
        'image': 'fedora:37',
        'platforms': ['linux/amd64', 'linux/arm64'],
    },
    'fedora:38': {
        'type': 'fedora',
        'image': 'fedora:38',
        'platforms': ['linux/amd64', 'linux/arm64'],
    },
    'fedora:39': {
        'type': 'fedora',
        'image': 'fedora:39',
        'platforms': ['linux/amd64', 'linux/arm64'],
    },
    'fedora:40': {
        'type': 'fedora',
        'image': 'fedora:40',
        'platforms': ['linux/amd64', 'linux/arm64'],
    },
    'fedora:latest': {
        'type': 'fedora',
        'image': 'fedora:latest',
        'platforms': ['linux/amd64', 'linux/arm64'],
    },
    'fedora:rawhide': {
        'type': 'fedora',
        'image': 'fedora:rawhide',
        'platforms': ['linux/amd64', 'linux/arm64'],
    },

    # openSUSE
    'opensuse-leap:15': {
        'type': 'opensuse',
        'image': 'opensuse/leap:15',
        'platforms': ['linux/amd64', 'linux/arm64'],
        'python_exe': 'python3.9',
        'setup_lines': [
            'RUN zypper install -y python39 python39-devel',
        ],
    },
    'opensuse-leap:latest': {
        'type': 'opensuse',
        'image': 'opensuse/leap:latest',
        'platforms': ['linux/amd64', 'linux/arm64'],
        'expect_success': False,
    },
    'opensuse-tumbleweed:latest': {
        'type': 'opensuse',
        'image': 'opensuse/tumbleweed:latest',
        'platforms': ['linux/amd64', 'linux/arm64'],
    },

    # Red Hat Linux Enterprise
    'rhel-ubi8': {
        'type': 'rhel',
        'image': 'redhat/ubi8',
        'platforms': ['linux/amd64', 'linux/arm64'],
        'python_exe': 'python3.8',
        'setup_lines': [
            'RUN yum install -y python38 python38-devel',
        ],
    },

    'rhel-ubi9': {
        'type': 'rhel',
        'image': 'redhat/ubi9',
        'platforms': ['linux/amd64', 'linux/arm64'],
    },

    # Rocky Linux
    'rockylinux:8': {
        'type': 'rockylinux',
        'image': 'rockylinux:8',
        'platforms': ['linux/amd64', 'linux/arm64'],
        'python_exe': 'python3.8',
        'setup_lines': [
            'RUN dnf module -y install python38',
            'RUN dnf install -y python38-devel',
        ],
    },
    'rockylinux:9': {
        'type': 'rockylinux',
        'image': 'rockylinux:9',
        'platforms': ['linux/amd64', 'linux/arm64'],
    },

    # Ubuntu Linux
    'ubuntu:18.04': {
        'type': 'ubuntu',
        'image': 'ubuntu:18.04',
        'platforms': ['linux/amd64', 'linux/arm64'],
        'python_exe': 'python3.8',
        'setup_lines': [
            ('RUN apt-get update &&'
             ' apt-get install -y software-properties-common'),
            'RUN add-apt-repository -y ppa:deadsnakes/ppa',
            'RUN apt-get install -y python3.8 python3.8-dev python3.8-venv',
        ],
    },
    'ubuntu:20.04': {
        'type': 'ubuntu',
        'image': 'ubuntu:20.04',
        'platforms': ['linux/amd64', 'linux/arm64'],
    },
    'ubuntu:22.04': {
        'type': 'ubuntu',
        'image': 'ubuntu:22.04',
        'platforms': ['linux/amd64', 'linux/arm64'],
    },
    'ubuntu:23.10': {
        'type': 'ubuntu',
        'image': 'ubuntu:23.10',
        'platforms': ['linux/amd64', 'linux/arm64'],
    },
    'ubuntu:latest': {  # Maps to the latest LTS
        'type': 'ubuntu',
        'image': 'ubuntu:latest',
        'platforms': ['linux/amd64', 'linux/arm64'],
    },
    'ubuntu:rolling': {
        'type': 'ubuntu',
        'image': 'ubuntu:rolling',
        'platforms': ['linux/amd64', 'linux/arm64'],
    },
}


NORM_ID_RE = re.compile(r'[^A-Za-z0-9]')


class BuildResult(Enum):
    SUCCEEDED = 1
    FAILED = 2
    ERROR = 3


@dataclass
class Build:
    #: The base image used for the Dockerfile.
    base_image: str

    #: Whether to expect a successful result from the build.
    expect_success: bool

    #: The path where logs will be stored.
    log_dir: str

    #: The name of the build.
    name: str

    #: Options for the distribution type.
    dist_type_options: Dict[str, Any]

    #: Options for the distribution.
    dist_options: Dict[str, Any]

    #: The platform to build for.
    platform: str

    #: The temp directory to build within.
    tmpdir: str

    #: Whether to show verbose log output from the build.
    verbose: bool

    #: The resulting build status.
    result: Optional[BuildResult] = None

    def __str__(self) -> str:
        return f'{self.name} ({self.platform})'


def build_dist(
    build: Build,
) -> None:
    """Build a distribution in Docker.

    This will generate a Dockerfile from the installation steps for the
    distribution and then attempt to build it.

    Args:
        build (Build):
            The build information and storage for the result.
    """
    setup_lines: List[str] = []

    setup_lines += (
        common_setup_lines +
        package_manager_setup_lines.get(
            build.dist_type_options['package_type'],
            []) +
        build.dist_options.get('setup_lines', []) +
        build.dist_type_options.get('setup_lines', [])
    )

    expect_success = build.expect_success
    verbose = build.verbose
    python = build.dist_options.get('python_exe', 'python3')

    base_image = build.base_image
    norm_build_name = NORM_ID_RE.sub('_', build.name)
    norm_platform = NORM_ID_RE.sub('_', build.platform)

    image_dir = os.path.join(build.tmpdir,
                             f'rb-{norm_build_name}_{norm_platform}')
    log_file = os.path.join(build.log_dir,
                            f'{norm_build_name}_{norm_platform}.log')
    dockerfile = os.path.join(image_dir, 'Dockerfile')

    # Prepare the Dockerfile and environment.
    os.mkdir(image_dir, 0o700)
    shutil.copy(
        os.path.abspath(os.path.join(__file__, '..', '..', 'dist',
                                     'rbinstall.py')),
        os.path.join(image_dir, 'rbinstall.py'))

    lines = [
        f'FROM {base_image}\n',
        *setup_lines,
        'ENV FOO=123',
        'RUN cat /etc/os-release',
        'RUN python3 --version',
        'ENV PYTHONUNBUFFERED=1',
        'ENV RBINSTALL_DEBUG=1',
        'ADD --chmod=755 rbinstall.py /tmp/rbinstall.py',
        f'RUN {python} /tmp/rbinstall.py --noinput',
    ]

    with open(dockerfile, 'w') as fp:
        fp.write('\n'.join(lines))

    # Prepare the build command.
    command = [
        'docker', 'buildx', 'build',
        '--progress', 'plain',
        '--platform', build.platform,
        '.',
    ]

    # Begin the build.
    stdout = sys.stdout
    stdout_buffer = stdout.buffer

    if build.verbose:
        print()
        print()

    print(f'{YELLOW}⏳ Building {build}...{RESET}')

    with open(log_file, 'wb') as fp:
        fp.write('\n'.join(lines).encode('utf-8'))
        fp.write(b'\n\n')

        with subprocess.Popen(command,
                              cwd=image_dir,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT) as p:
            assert p.stdout is not None

            while p.poll() is None:
                data = p.stdout.read1()
                fp.write(data)

                if verbose:
                    stdout_buffer.write(data)
                    stdout_buffer.flush()

            # Write out anything that's remaining.
            data = p.stdout.read()
            fp.write(data)

            if verbose:
                stdout_buffer.write(data)
                stdout_buffer.flush()

            rc = p.wait()

    # Process the results of the build.
    if rc not in (0, 1):
        build.result = BuildResult.ERROR
    elif ((expect_success and rc == 0) or
          (not expect_success and rc == 1)):
        build.result = BuildResult.SUCCEEDED
    else:
        build.result = BuildResult.FAILED


def run_builds(
    builds: List[Build],
    parallel: bool,
    max_parallel: int = 2,
) -> Iterator[Build]:
    if parallel:
        with ThreadPoolExecutor(max_workers=max_parallel) as executor:
            futures_to_build = {
                executor.submit(build_dist, build): build
                for build in builds
            }

            for future in as_completed(futures_to_build):
                yield futures_to_build[future]
    else:
        for build in builds:
            build_dist(build)
            yield build


def main() -> None:
    """Main entrypoint for the installation tests."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--log-dir',
        metavar='PATH',
        default=os.path.abspath(os.path.join(__file__, '..', 'logs')),
        help='The directory where logs will be stored')
    parser.add_argument(
        '-p',
        '--parallel',
        action='store_true',
        help=(
            'Run builds in parallel. Note that this will disable verbose '
            'logging.'
        ))
    parser.add_argument(
        '-c',
        '--max-parallel',
        metavar='NUM',
        default=max(int((os.cpu_count() or 1) * 0.75), 1),
        help=(
            "Maximum number of tests to run in parallel when using -p. If "
            "not specified, the default will be 3/4th of the system's CPUs."
        ))
    parser.add_argument(
        '--lf',
        dest='last_failed',
        action='store_true',
        help=(
            "Whether to only run builds that failed last time."
        ))
    parser.add_argument(
        '--platforms',
        metavar='PLATFORM[,PLATFORM...]',
        default='linux/arm64,linux/amd64',
        help='A comma-separated list of Docker platforms to build.')
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Whether to show output from the Docker builds.')
    parser.add_argument(
        'dist',
        nargs='*',
        default='all',
        choices=(
            ['all'] +
            sorted(DIST_TYPES.keys()) +
            sorted(DISTS.keys())
        ))

    args = parser.parse_args()
    last_failed = args.last_failed
    log_dir = args.log_dir
    parallel = args.parallel
    platforms_set = set(args.platforms.split(','))
    verbose = args.verbose and not parallel

    # Determine which distributions we'll be testing with.
    if 'all' in args.dist:
        dists = sorted(DISTS.keys())
    else:
        dists = []

        for dist_name in args.dist:
            dists += [
                _image
                for _image, _dist_info in DISTS.items()
                if _image == dist_name or _dist_info['type'] == dist_name
            ]

        dists = sorted(set(dists))

    # If running in last-failed mode, filter that by the ones that last failed.
    if last_failed:
        try:
            with open('.rbinstall-test-state', 'r') as fp:
                test_state = json.load(fp)
        except IOError:
            test_state = {}

        last_failed_builds = set(
            (_build_state['name'], _build_state['platform'])
            for _build_state in chain.from_iterable([
                test_state.get('failed_builds', []),
                test_state.get('error_builds', []),
            ])
        )

        dists = [
            _dist
            for _dist in dists
            if any(
                (_dist, _platform) in last_failed_builds
                for _platform in platforms_set
            )
        ]

    # Prepare information on all the pending builds.
    tmpdir = tempfile.mkdtemp(prefix='rbinstall-tests')

    if not os.path.exists(log_dir):
        os.makedirs(log_dir, 0o755)

    succeeded_builds: List[Build] = []
    failed_builds: List[Build] = []
    error_builds: List[Build] = []
    pending_builds: List[Build] = []

    for dist in dists:
        dist_info = DISTS[dist]

        for platform in dist_info.get('platforms', ['linux/amd64']):
            if platform in platforms_set:
                pending_builds.append(Build(
                    tmpdir=tmpdir,
                    base_image=dist_info['image'],
                    name=dist,
                    platform=platform,
                    expect_success=dist_info.get('expect_success', True),
                    dist_type_options=DIST_TYPES[dist_info['type']],
                    dist_options=dist_info,
                    log_dir=log_dir,
                    verbose=verbose))

    # Run through the builds.
    num_builds = len(pending_builds)

    if num_builds == 1:
        print('Running 1 install test...')
    else:
        print(f'Running {num_builds} install tests...')

    for build in run_builds(pending_builds,
                            parallel=parallel,
                            max_parallel=args.max_parallel):
        platform = build.platform
        result = build.result

        if verbose:
            print()
            print()

        if result == BuildResult.SUCCEEDED:
            succeeded_builds.append(build)

            if build.expect_success:
                print(f'{GREEN}✅ {build} build succeeded!{RESET}')
            else:
                print(f'{GREEN}✅ {build} build failed as expected!{RESET}')
        elif result == BuildResult.FAILED:
            failed_builds.append(build)

            if build.expect_success:
                print(f'{RED}❌ {build} build failed!{RESET}')
            else:
                print(f'{RED}❌ {build} build surprisingly succeeded! Kinda '
                      f'sus...{RESET}')
        elif result == BuildResult.ERROR:
            error_builds.append(build)

            print(f'{RED}⚠️  {build} build had an unexpected error!{RESET}')

    # Clean up.
    shutil.rmtree(tmpdir)

    # Report a summary of the statuses of the builds that were run.
    for builds, color, status in ((succeeded_builds, GREEN, 'succeeded'),
                                  (failed_builds, RED, 'failed'),
                                  (error_builds, RED, 'unexpectedly errored')):
        if builds:
            print()

            num_builds = len(builds)

            if num_builds == 1:
                print(f'{color}1 build {status}:{RESET}')
            else:
                print(f'{color}{num_builds} builds {status}:{RESET}')

            print()

            for build in sorted(builds, key=lambda build: build.name):
                print(f'    {color}{build}{RESET}')

    print()
    print(f'Logs are stored in {log_dir}')

    with open('.rbinstall-test-state', 'w') as fp:
        json.dump(
            {
                _key: [
                    {
                        'name': _build.name,
                        'platform': _build.platform,
                    }
                    for _build in _builds
                ]
                for _key, _builds in (('succeeded_builds', succeeded_builds),
                                      ('failed_builds', failed_builds),
                                      ('error_builds', error_builds))
            },
            fp)


if __name__ == '__main__':
    main()
