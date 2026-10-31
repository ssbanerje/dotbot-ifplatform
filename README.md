# dotbot-ifplatform

Conditional execution of [`dotbot`](https://github.com/anishathalye/dotbot) directives based on the local operating system or Linux/BSD distribution.

## Prerequisites

This plugin requires [`dotbot`](https://github.com/anishathalye/dotbot) to be installed.

## Installation

1. Add the plugin as a submodule to your dotfiles repository:
   ```sh
   git submodule add https://github.com/ssbanerje/dotbot-ifplatform.git
   ```
2. (Recommended) Initialize the embedded [`distro`](https://github.com/python-distro/distro) submodule:
   ```sh
   git submodule update --init --recursive
   ```
   > If the `lib/distro` submodule is not initialized, `dotbot-ifplatform` automatically falls back to Python's standard library (`sys.platform`, `platform.system()`, and `platform.freedesktop_os_release()` / `/etc/os-release`).
3. Load the plugin either in your Dotbot YAML config (**Dotbot v1.21+**, recommended):
   ```yaml
   - plugins:
       - dotbot-ifplatform/ifplatform.py
   ```
   or via the CLI when invoking `dotbot`:
   ```sh
   dotbot -p dotbot-ifplatform/ifplatform.py -c install.conf.yaml
   ```
   *(Legacy `--plugin-dir dotbot-ifplatform` is also supported.)*

## Usage

Add `if<platform>` or `ifnot<platform>` blocks to your Dotbot YAML configuration to conditionally execute nested directives. Top-level `- defaults:`, `--dry-run`, `--exit-on-failure`, and YAML-loaded `- plugins:` are automatically inherited inside matching blocks.

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

- ifwindows:
    - shell:
        - winget install Git.Git

- ifnotwindows:
    - link:
        ~/.bashrc: shell/bashrc

- ifanylinux:
    - ifnotwsl:
        - link:
            ~/.config/i3/config: i3/config
```

### Derivative Distributions (`ID_LIKE`) & WSL

- **`ID_LIKE` matching:** Derivative distributions match both their own ID and any parent distribution listed in `ID_LIKE`. For example, CachyOS matches `ifcachyos`, `ifarch`, and `ifanylinux`; Linux Mint and Pop!_OS match their own directives as well as `ifubuntu`, `ifdebian`, and `ifanylinux`.
- **Additive WSL matching:** When running inside Windows Subsystem for Linux (e.g., Ubuntu on WSL2), `ifwsl`, `ifubuntu`, and `ifanylinux` all match, while `ifnotwsl` allows skipping Linux desktop-only steps.

### Supported `<platform>` Values

Every entry below supports both `if<platform>` and `ifnot<platform>`.

#### Meta & OS Targets

| `<platform>` | Description                                              |
|--------------|----------------------------------------------------------|
| `any`        | Any platform                                             |
| `anylinux`   | Any Linux distribution                                   |
| `anybsd`     | Any BSD distribution                                     |
| `wsl`        | Windows Subsystem for Linux (additive on Linux)          |
| `macos`      | macOS                                                    |
| `windows`    | Windows                                                  |
| `aix`        | IBM AIX                                                  |

#### Linux Distributions

| `<platform>`  | Description                                             |
|---------------|---------------------------------------------------------|
| `almalinux`   | AlmaLinux                                               |
| `alpine`      | Alpine Linux                                            |
| `altlinux`    | ALT Linux                                               |
| `amzn`        | Amazon Linux (`amazon` is also accepted as an alias)    |
| `amazon`      | Amazon Linux (legacy alias for `amzn`)                  |
| `arch`        | Arch Linux                                              |
| `bazzite`     | Bazzite                                                 |
| `buildroot`   | Buildroot                                               |
| `cachyos`     | CachyOS                                                 |
| `centos`      | CentOS                                                  |
| `cloudlinux`  | CloudLinux OS                                           |
| `debian`      | Debian                                                  |
| `elementary`  | Elementary OS                                           |
| `endeavouros` | EndeavourOS                                             |
| `exherbo`     | Exherbo Linux                                           |
| `fedora`      | Fedora                                                  |
| `garuda`      | Garuda Linux                                            |
| `gentoo`      | Gentoo Linux                                            |
| `guix`        | Guix System                                             |
| `ibm_powerkvm`| IBM PowerKVM                                            |
| `kali`        | Kali Linux                                              |
| `kvmibm`      | KVM for IBM z Systems                                   |
| `linuxmint`   | Linux Mint                                              |
| `mageia`      | Mageia                                                  |
| `mandriva`    | Mandriva Linux                                          |
| `manjaro`     | Manjaro Linux                                           |
| `nixos`       | NixOS                                                   |
| `nobara`      | Nobara Linux                                            |
| `opensuse`    | openSUSE                                                |
| `oracle`      | Oracle Linux (and Oracle Enterprise Linux)              |
| `parallels`   | Parallels                                               |
| `pidora`      | Pidora                                                  |
| `pop`         | Pop!_OS                                                 |
| `raspbian`    | Raspbian                                                |
| `rhel`        | Red Hat Enterprise Linux                                |
| `rocky`       | Rocky Linux                                             |
| `scientific`  | Scientific Linux                                        |
| `slackware`   | Slackware                                               |
| `sles`        | SUSE Linux Enterprise Server                            |
| `solus`       | Solus                                                   |
| `steamos`     | SteamOS                                                 |
| `ubuntu`      | Ubuntu                                                  |
| `void`        | Void Linux                                              |
| `xenserver`   | XenServer                                               |
| `zorin`       | Zorin OS                                                |

#### BSD Distributions

| `<platform>`  | Description                                             |
|---------------|---------------------------------------------------------|
| `dragonfly`   | DragonFly BSD                                           |
| `freebsd`     | FreeBSD                                                 |
| `midnightbsd` | MidnightBSD                                             |
| `netbsd`      | NetBSD                                                  |
| `openbsd`     | OpenBSD                                                 |
