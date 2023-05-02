#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import os
import sys
import dotbot
from dotbot.dispatcher import Dispatcher
from dotbot.util import module
from dotbot.plugins import Clean, Create, Link, Shell


def _inject_distro():
    # Find distro in submodule
    root_dir = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join(root_dir, 'lib/distro/src/distro')
    # Update path
    sys.path.insert(0, path)


_inject_distro()
import distro


class IfPlatform(dotbot.Plugin):
    _distros = [
        'anylinux',     # All linux
        'anybsd',       # All BSD
        'macos',        # MacOS
        'ubuntu',       # Ubuntu
        'debian',       # Debian
        'rhel',         # RedHat Enterprise Linux
        'centos',       # CentOS
        'fedora',       # Fedora
        'sles',         # SUSE Linux Enterprise Server
        'opensuse',     # openSUSE
        'amazon',       # Amazon Linux
        'arch',         # Arch Linux
        'cloudlinux',   # CloudLinux OS
        'exherbo',      # Exherbo Linux
        'gentoo',       # GenToo Linux
        'ibm_powerkvm', # IBM PowerKVM
        'kvmibm',       # KVM for IBM z Systems
        'linuxmint',    # Linux Mint
        'mageia',       # Mageia
        'mandriva',     # Mandriva Linux
        'parallels',    # Parallels
        'pidora',       # Pidora
        'raspbian',     # Raspbian
        'oracle',       # Oracle Linux (and Oracle Enterprise Linux)
        'scientific',   # Scientific Linux
        'slackware',    # Slackware
        'xenserver',    # XenServer
        'openbsd',      # OpenBSD
        'netbsd',       # NetBSD
        'freebsd',      # FreeBSD
        'midnightbsd',  # MidnightBSD
    ]

    def __init__(self, context):
        super(IfPlatform, self).__init__(context)
        self._directives = ['if'+d for d in self._distros]
        self._bsd = [d for d in self._distros if d.endswith('bsd')]
        self._linux = [d for d in self._distros if (d not in self._bsd) and (d != 'macos')]

    def _load_plugins(self):
        plugin_paths = self._context.options().plugins
        plugins = []
        for dir in self._context.options().plugin_dirs:
            for path in glob.glob(os.path.join(dir, '*.py')):
                plugin_paths.append(path)
        for path in plugin_paths:
            abspath = os.path.abspath(path)
            plugins.extend(module.load(abspath))
        if not self._context.options().disable_built_in_plugins:
            plugins.extend([Clean, Create, Link, Shell])
        return plugins

    def can_handle(self, directive):
        return directive in self._directives

    def handle(self, directive, data):
        if directive not in self._directives:
            raise ValueError('Cannot handle this directive %s' % directive)

        did = distro.id()
        if did == 'darwin':
            did = 'macos'

        if (directive == 'ifanylinux' and did in self._linux) or \
                (directive == 'ifanybsd' and did in self._bsd) or \
                (directive == 'if'+did):
            self._log.debug('Matched platform %s' % did)
            return self._run_internal(data)
        else:
            return True

    def _run_internal(self, data):
        dispatcher = Dispatcher(self._context.base_directory(),
                                only=self._context.options().only,
                                skip=self._context.options().skip,
                                options=self._context.options(),
                                plugins=self._load_plugins())
        return dispatcher.dispatch(data)
