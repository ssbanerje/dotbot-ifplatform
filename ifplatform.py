#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import os
import sys

import dotbot
from dotbot.dispatcher import Dispatcher
from dotbot.plugins import Clean, Create, Link, Shell
from dotbot.util import module


def _inject_distro():
    root_dir = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.join(root_dir, 'lib', 'distro', 'src', 'distro'))


_inject_distro()
import distro  # noqa: E402


class IfPlatform(dotbot.Plugin):
    _distros = [
        'anylinux',      # All linux
        'anybsd',        # All BSD
        'macos',         # MacOS
        'windows',       # Windows
        'ubuntu',        # Ubuntu
        'debian',        # Debian
        'rhel',          # RedHat Enterprise Linux
        'centos',        # CentOS
        'fedora',        # Fedora
        'sles',          # SUSE Linux Enterprise Server
        'opensuse',      # openSUSE
        'amazon',        # Amazon Linux
        'arch',          # Arch Linux
        'cloudlinux',    # CloudLinux OS
        'exherbo',       # Exherbo Linux
        'elementary',    # Elementary OS
        'gentoo',        # GenToo Linux
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
        'openbsd',       # OpenBSD
        'netbsd',        # NetBSD
        'freebsd',       # FreeBSD
        'midnightbsd',   # MidnightBSD
        'alpine',        # Alpine Linux
        'rocky',         # Rocky Linux
    ]

    def __init__(self, context):
        super(IfPlatform, self).__init__(context)
        self._directives = {'if' + d for d in self._distros}
        self._bsd = {d for d in self._distros if d.endswith('bsd')}
        self._linux = {
            d for d in self._distros if (d not in self._bsd) and (d not in {'macos', 'windows'})
        }
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

        did = distro.id()
        if did == 'darwin' or sys.platform == 'darwin':
            did = 'macos'
        elif os.name == 'nt':
            did = 'windows'

        # Include ID_LIKE entries so derivatives (e.g. CachyOS -> arch) match
        all_ids = [did] + distro.like().split()
        is_linux = sys.platform.startswith('linux') or any(d in self._linux for d in all_ids)
        is_bsd = any(d in self._bsd for d in all_ids)

        if (
            (directive == 'ifanylinux' and is_linux)
            or (directive == 'ifanybsd' and is_bsd)
            or any(directive == 'if' + d for d in all_ids)
        ):
            self._log.debug('Matched platform %s' % did)
            return self._run_internal(data)
        return True

    def _run_internal(self, data):
        dispatcher = Dispatcher(
            self._context.base_directory(),
            only=self._context.options().only,
            skip=self._context.options().skip,
            options=self._context.options(),
            plugins=self._get_plugins(),
        )
        return dispatcher.dispatch(data)
