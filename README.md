Review Board Installer
======================

The Review Board Installer, rbinstall, is designed to simplify installing
[Review Board](https://www.reviewboard.org/) on a wide variety of Linux
distributions.

Installation can be performed with a single command:

```shell
$ curl https://install.reviewboard.org | python3
```

Alternatively, you can run:

```shell
$ pipx run rbinstall
```

The installer must be run as `root`.


Compatibility
-------------

rbinstall requires a supported Linux or macOS system with Python 3.7 or higher.

**NOTE:** If you're using a non-default version of Python, you will need to use
a web server such as [gunicorn](https://gunicorn.org/),
[uwsgi](https://uwsgi-docs.readthedocs.io/en/latest/), or build an Apache
`mod_wsgi` for your server using
[mod_wsgi-express](https://pypi.org/project/mod-wsgi/).


### Linux Compatibility

The following Linux distributions are directly supported on a default install:

* Amazon Linux 2023
* CentOS 9 Stream
* CentOS 10 Stream
* Debian 11 (Bullseye)
* Debian 12 (Bookworm)
* Debian 13 (Trixie)
* Fedora 42
* Fedora 43
* openSUSE Leap 16
* openSUSE Tumbleweed
* Red Hat Enterprise Linux 9
* Red Hat Enterprise Linux 10
* Rocky Linux 9
* Rocky Linux 10
* Ubuntu 22.04 LTS
* Ubuntu 24.04 LTS
* Ubuntu 25.10


The following do not currently work because they ship Python 3.14, which is not
currently supported by Review Board. They should work if you manually install
Python 3.13:

* Arch Linux
* Fedora Rawhide


The following are known to work if you install a newer version of Python
(see below):

* openSUSE Leap 15
* Red Hat Enterprise Linux 8
* Rocky Linux 8


The following Linux distributions are end-of-life, but are known to work:

* Amazon Linux 2 (requires a newer Python, see below)
* CentOS 8
* CentOS 8 Stream
* Debian 10
* Fedora 36-41
* Ubuntu 18.04 LTS (requires a newer Python, see below)
* Ubuntu 20.04 LTS
* Other non-LTS Ubuntu versions.


### macOS Compatibility

The following versions of macOS have been tested:

* macOS Ventura
* macOS Sonoma

[Homebrew](https://brew.sh) is currently required for installation on macOS.


Legacy Distro Notes
-------------------

### Amazon Linux 2

Before installing on Amazon Linux 2, you will need to install a newer version
of Python:

```shell
sudo amazon-linux-extras install python3.8
sudo yum install python38-devel
```

Then run the installation script with `python3.8`.

Please note that Python 3.8 reaches end-of-life on October 14, 2024. Versions
of Review Board after this date may no longer support Python 3.8.


### openSUSE Leap 15

Before installing on openSUSE Leap 15, you will need to install a newer version
of Python:

```shell
sudo zypper install python39 python39-devel
```

Then run the installation script with `python3.9`.


### Red Hat Enterprise Linux 8

Before installing on Red Hat Enterprise Linux 8, you will need to install a newer version
of Python:

```shell
sudo yum install -y python38 python38-devel
```

Then run the installation script with `python3.8`.

Note that due to missing packages, Single Sign-On is not available on
Red Hat Enterprise Linux 8.

Please note that Python 3.8 reaches end-of-life on October 14, 2024. Versions
of Review Board after this date may no longer support Python 3.8.


### Rocky Linux 8

Before installing on Rocky Linux 8, you will need to install a newer version
of Python:

```shell
sudo dnf module install python38
sudo dnf install python38-devel
```

Then run the installation script with `python3.8`.

Note that due to missing packages, Single Sign-On is not available on
Rocky Linux 8.

Please note that Python 3.8 reaches end-of-life on October 14, 2024. Versions
of Review Board after this date may no longer support Python 3.8.


### Ubuntu 18.04

Before installing on Ubuntu 18.04, you will need to install a newer version
of Python:

```shell
sudo apt-get install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get install python3.8 python3.8-dev python3.8-venv
```

Then run the installation script with `python3.8`.

Note that due to missing packages, Single Sign-On is not available on
Ubuntu 18.04.

Please note that Python 3.8 reaches end-of-life on October 14, 2024. Versions
of Review Board after this date may no longer support Python 3.8.
