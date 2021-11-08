# dotbot-ifplatform

Conditional execution of dotbot directives based on the local platform.


## Prerequisites
This plugin requires [`dotbot`](https://github.com/anishathalye/dotbot) to be installed.

## Installation
1. Run `git submodule add https://github.com/ssbanerje/dotbot-ifplatform.git`
2. Run `git submodule update --init --recursive`
3. Pass in the CLI argument `--plugin-dir dotbot-ifplatform` when executing the `dotbot` executable.


## Usage

Add the `if<platform>` directive to the `dotbot` YAML file to conditionally execute the directives.
For example:

```yaml
- ifubuntu:
    - apt:
        - ranger

- ifarch:
    - pacman:
        - ranger

- ifmacos:
    - brew:
        - ranger
```

### Details

The plugin queries the local platform string using the `distro` plugin. Acceptable values of
`<platform>` in the `if<platform>` directive is shown below:

| `<platform>` | Description                                |
|--------------|--------------------------------------------|
| anylinux     | Any Linux in table                         |
| anybsd       | Any BSD in table                           |
| macos        | MacOS                                      |
| ubuntu       | Ubuntu                                     |
| debian       | Debian                                     |
| rhel         | RedHat Enterprise Linux                    |
| centos       | CentOS                                     |
| fedora       | Fedora                                     |
| sles         | SUSE Linux Enterprise Server               |
| opensuse     | openSUSE                                   |
| amazon       | Amazon Linux                               |
| arch         | Arch Linux                                 |
| cloudlinux   | CloudLinux OS                              |
| elementary   | Elementary OS                              |
| exherbo      | Exherbo Linux                              |
| gentoo       | GenToo Linux                               |
| ibm_powerkvm | IBM PowerKVM                               |
| kvmibm       | KVM for IBM z Systems                      |
| linuxmint    | Linux Mint                                 |
| mageia       | Mageia                                     |
| mandriva     | Mandriva Linux                             |
| parallels    | Parallels                                  |
| pidora       | Pidora                                     |
| raspbian     | Raspbian                                   |
| oracle       | Oracle Linux (and Oracle Enterprise Linux) |
| scientific   | Scientific Linux                           |
| slackware    | Slackware                                  |
| xenserver    | XenServer                                  |
| openbsd      | OpenBSD                                    |
| netbsd       | NetBSD                                     |
| freebsd      | FreeBSD                                    |
| midnightbsd  | MidnightBSD                                |

This list was generated using `distro` v1.6.0. There might be some differences based on the version
of `distro` installed locally.
