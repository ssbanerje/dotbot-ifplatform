#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import inspect
import os
import platform
import sys

import dotbot
from dotbot.dispatcher import Dispatcher
from dotbot.plugins import Clean, Create, Link, Shell
from dotbot.util import module


def _inject_distro():
    root_dir = os.path.dirname(os.path.realpath(__file__))
    distro_src = os.path.join(root_dir, 'lib', 'distro', 'src')
    if os.path.isdir(os.path.join(distro_src, 'distro')) and distro_src not in sys.path:
        sys.path.insert(0, distro_src)


_inject_distro()
try:
    import distro  # noqa: E402
except ImportError:
    distro = None


_NORMALIZED_OS_ID = {
    'ol': 'oracle',
    'opensuse-leap': 'opensuse',
}
_OS_RELEASE_PATHS = ('/etc/os-release', '/usr/lib/os-release')


def _parse_os_release_lines(lines):
    info = {}
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        value = value.replace('\\"', '"').replace("\\'", "'").replace('\\\\', '\\')
        info[key.strip()] = value
    return info


def _read_os_release():
    if hasattr(platform, 'freedesktop_os_release'):
        try:
            return platform.freedesktop_os_release()
        except OSError:
            pass
    for path in _OS_RELEASE_PATHS:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return _parse_os_release_lines(f)
        except OSError:
            continue
    return {}


def _stdlib_distro_info():
    info = _read_os_release() if sys.platform.startswith('linux') else {}
    raw_id = info.get('ID', '').strip().lower().replace(' ', '_')
    if raw_id:
        did = _NORMALIZED_OS_ID.get(raw_id, raw_id)
    else:
        did = platform.system().lower().replace(' ', '_')
    like_ids = [entry.lower() for entry in info.get('ID_LIKE', '').split()]
    return did, like_ids


def _is_wsl(is_linux):
    if not is_linux:
        return False
    if 'WSL_DISTRO_NAME' in os.environ or 'WSL_INTEROP' in os.environ:
        return True
    try:
        release = platform.release().lower()
    except Exception:
        release = ''
    return 'microsoft' in release or 'wsl' in release


class IfPlatform(dotbot.Plugin):
    supports_dry_run = True

    _meta_targets = (
        'any',           # Any platform
        'anylinux',      # All Linux distributions
        'anybsd',        # All BSD distributions
        'wsl',           # Windows Subsystem for Linux
    )
    _os_targets = (
        'macos',         # macOS
        'windows',       # Windows
        'aix',           # AIX
    )
    _bsd_distros = (
        'openbsd',       # OpenBSD
        'netbsd',        # NetBSD
        'freebsd',       # FreeBSD
        'midnightbsd',   # MidnightBSD
        'dragonfly',     # DragonFly BSD
    )
    _linux_distros = (
        'ubuntu',        # Ubuntu
        'debian',        # Debian
        'rhel',          # RedHat Enterprise Linux
        'centos',        # CentOS
        'fedora',        # Fedora
        'sles',          # SUSE Linux Enterprise Server
        'opensuse',      # openSUSE
        'amzn',          # Amazon Linux (distro.id() / os-release ID)
        'amazon',        # Amazon Linux (legacy alias)
        'arch',          # Arch Linux
        'buildroot',     # Buildroot
        'cloudlinux',    # CloudLinux OS
        'exherbo',       # Exherbo Linux
        'elementary',    # Elementary OS
        'gentoo',        # GenToo Linux
        'guix',          # Guix System
        'altlinux',      # ALT Linux
        'ibm_powerkvm',  # IBM PowerKVM
        'kvmibm',        # KVM for IBM z Systems
        'linuxmint',     # Linux Mint
        'mageia',        # Mageia
        'mandriva',      # Mandriva Linux
        'parallels',     # Parallels
        'pidora',        # Pidora
        'raspbian',      # Raspbian
        'oracle',        # Oracle Linux (and Oracle Enterprise Linux)
        'scientific',    # Scientific Linux
        'slackware',     # Slackware
        'xenserver',     # XenServer
        'alpine',        # Alpine Linux
        'rocky',         # Rocky Linux
        'almalinux',     # AlmaLinux
        'void',          # Void Linux
        'pop',           # Pop!_OS
        'manjaro',       # Manjaro Linux
        'nixos',         # NixOS
        'kali',          # Kali Linux
        'cachyos',       # CachyOS
        'endeavouros',   # EndeavourOS
        'garuda',        # Garuda Linux
        'nobara',        # Nobara Linux
        'bazzite',       # Bazzite
        'steamos',       # SteamOS
        'zorin',         # Zorin OS
        'solus',         # Solus
    )
    _distros = list(_meta_targets + _os_targets + _linux_distros + _bsd_distros)

    def __init__(self, context):
        super(IfPlatform, self).__init__(context)
        self._targets = set(self._distros)
        self._directives = (
            {'if' + d for d in self._targets}
            | {'ifnot' + d for d in self._targets}
        )
        self._bsd = set(self._bsd_distros)
        self._linux = set(self._linux_distros)
        self._other_os = set(self._os_targets) | self._bsd
        self._plugins = None

    def _get_plugins(self):
        if hasattr(self._context, 'plugins'):
            ctx_plugins = self._context.plugins()
            if ctx_plugins is not None:
                return ctx_plugins
        return self._load_plugins()

    def _load_plugins(self):
        if self._plugins is not None:
            return self._plugins

        plugin_paths = list(self._context.options().plugins)
        for plugin_dir in self._context.options().plugin_dirs:
            plugin_paths.extend(glob.glob(os.path.join(plugin_dir, '*.py')))

        plugins = []
        for path in plugin_paths:
            abspath = os.path.abspath(path)
            for plugin in module.load(abspath):
                if plugin not in plugins:
                    plugins.append(plugin)
        if not self._context.options().disable_built_in_plugins:
            for builtin in [Clean, Create, Link, Shell]:
                if builtin not in plugins:
                    plugins.append(builtin)

        self._plugins = plugins
        return self._plugins

    def can_handle(self, directive):
        return directive in self._directives

    def handle(self, directive, data):
        if directive not in self._directives:
            raise ValueError('Cannot handle this directive %s' % directive)

        if sys.platform == 'darwin':
            did, like_ids = 'macos', []
        elif os.name == 'nt' or sys.platform in ('win32', 'cygwin', 'msys'):
            did, like_ids = 'windows', []
        elif distro is not None:
            did = distro.id()
            like_ids = distro.like().split()
        else:
            did, like_ids = _stdlib_distro_info()

        if did == 'darwin':
            did = 'macos'
        elif did in ('windows', 'win32', 'nt') or did.startswith(('msys', 'mingw', 'cygwin')):
            did = 'windows'

        # Include ID_LIKE entries so derivatives (e.g. CachyOS -> arch) match
        all_ids = [did] + like_ids if did else list(like_ids)
        if 'amzn' in all_ids and 'amazon' not in all_ids:
            all_ids.append('amazon')
        elif 'amazon' in all_ids and 'amzn' not in all_ids:
            all_ids.append('amzn')

        is_linux = any(d in self._linux for d in all_ids) or (
            did not in self._other_os and sys.platform.startswith('linux')
        )
        is_bsd = any(d in self._bsd for d in all_ids)
        is_wsl = _is_wsl(is_linux)

        if directive.startswith('ifnot'):
            target, negate = directive[5:], True
        else:
            target, negate = directive[2:], False

        matched = (
            target == 'any'
            or (target == 'anylinux' and is_linux)
            or (target == 'anybsd' and is_bsd)
            or (target == 'wsl' and is_wsl)
            or (target in all_ids)
        )
        if negate:
            matched = not matched

        if matched:
            self._log.debug('Matched directive %s on platform %s' % (directive, did))
            return self._run_internal(data)
        return True

    def _run_internal(self, data):
        options = self._context.options()
        kwargs = {
            'only': options.only,
            'skip': options.skip,
            'options': options,
        }
        try:
            params = inspect.signature(Dispatcher.__init__).parameters
        except (TypeError, ValueError):
            params = {}
        accepts_var_kw = any(
            p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()
        )
        if accepts_var_kw or 'plugins' in params:
            kwargs['plugins'] = self._get_plugins()
        if accepts_var_kw or 'exit_on_failure' in params:
            kwargs['exit_on_failure'] = getattr(options, 'exit_on_failure', False)

        dispatcher = Dispatcher(self._context.base_directory(), **kwargs)
        defaults = self._context.defaults()
        if defaults and hasattr(dispatcher, '_context'):
            dispatcher._context.set_defaults(defaults)
        return dispatcher.dispatch(data)
