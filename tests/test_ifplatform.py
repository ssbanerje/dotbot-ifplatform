import contextlib
import io
import logging
import os
import sys
import unittest
from argparse import Namespace
from unittest.mock import MagicMock, patch


# dotbot isn't installed during unit tests, so mock it before ifplatform is imported
class _MockPlugin:
    supports_dry_run = False

    def __init__(self, context):
        self._context = context
        self._log = logging.getLogger('test.ifplatform')


_mock_dotbot = MagicMock()
_mock_dotbot.Plugin = _MockPlugin
sys.modules.setdefault('dotbot', _mock_dotbot)
sys.modules.setdefault('dotbot.dispatcher', MagicMock())
sys.modules.setdefault('dotbot.util', MagicMock())
sys.modules.setdefault('dotbot.util.module', MagicMock())
sys.modules.setdefault('dotbot.plugins', MagicMock())

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ifplatform  # noqa: E402
from ifplatform import IfPlatform, _parse_os_release_lines  # noqa: E402


def _make_plugin(with_context_plugins=False, context_plugins=None, defaults=None, exit_on_failure=False):
    options = Namespace(
        plugins=[],
        plugin_dirs=[],
        disable_built_in_plugins=True,
        only=None,
        skip=None,
        exit_on_failure=exit_on_failure,
        dry_run=False,
    )
    if with_context_plugins:
        context = MagicMock()
        context.plugins.return_value = context_plugins
    else:
        context = MagicMock(
            spec=['base_directory', 'options', 'defaults', 'set_defaults']
        )
    context.base_directory.return_value = '/tmp/dotfiles'
    context.options.return_value = options
    context.defaults.return_value = defaults if defaults is not None else {}
    return IfPlatform(context)


@contextlib.contextmanager
def _mock_distro(did, like=''):
    fake = MagicMock()
    fake.id.return_value = did
    fake.like.return_value = like
    with patch.object(ifplatform, 'distro', fake):
        yield fake


@contextlib.contextmanager
def _clean_wsl_env():
    env = {k: v for k, v in os.environ.items() if k not in ('WSL_DISTRO_NAME', 'WSL_INTEROP')}
    with patch.dict(os.environ, env, clear=True), patch(
        'ifplatform.platform.release', return_value='6.8.0-generic'
    ):
        yield


class TestDirectMatch(unittest.TestCase):
    """Native distro and OS IDs match their own directives."""

    def test_native_distros_match(self):
        for did in (
            'arch',
            'ubuntu',
            'pop',
            'void',
            'manjaro',
            'nixos',
            'almalinux',
            'rocky',
            'alpine',
            'kali',
            'buildroot',
            'guix',
            'altlinux',
        ):
            with self.subTest(did=did), _mock_distro(did):
                plugin = _make_plugin()
                with patch.object(plugin, '_run_internal', return_value=True) as run:
                    plugin.handle('if' + did, [])
                    run.assert_called_once()
                with patch.object(plugin, '_run_internal', return_value=True) as run:
                    plugin.handle('ifanylinux', [])
                    run.assert_called_once()

    def test_darwin_maps_to_ifmacos(self):
        with _mock_distro('darwin'):
            plugin = _make_plugin()
            with patch.object(plugin, '_run_internal', return_value=True) as run:
                plugin.handle('ifmacos', [])
                run.assert_called_once()
            with patch.object(plugin, '_run_internal', return_value=True) as run:
                plugin.handle('ifanylinux', [])
                run.assert_not_called()

    def test_windows_maps_to_ifwindows(self):
        with _mock_distro(''), patch('ifplatform.os.name', 'nt'), patch(
            'ifplatform.sys.platform', 'win32'
        ):
            plugin = _make_plugin()
            with patch.object(plugin, '_run_internal', return_value=True) as run:
                plugin.handle('ifwindows', [])
                run.assert_called_once()
            with patch.object(plugin, '_run_internal', return_value=True) as run:
                plugin.handle('ifanylinux', [])
                run.assert_not_called()

    def test_aix_does_not_match_anylinux_or_anybsd(self):
        with _mock_distro('aix'):
            plugin = _make_plugin()
            with patch.object(plugin, '_run_internal', return_value=True) as run:
                plugin.handle('ifaix', [])
                run.assert_called_once()
            for other in ('ifanylinux', 'ifanybsd', 'ifmacos', 'ifwindows'):
                with patch.object(plugin, '_run_internal', return_value=True) as run:
                    plugin.handle(other, [])
                    run.assert_not_called()

    def test_dragonfly_matches_bsd_only(self):
        with _mock_distro('dragonfly'):
            plugin = _make_plugin()
            for matching in ('ifdragonfly', 'ifanybsd'):
                with patch.object(plugin, '_run_internal', return_value=True) as run:
                    plugin.handle(matching, [])
                    run.assert_called_once()
            with patch.object(plugin, '_run_internal', return_value=True) as run:
                plugin.handle('ifanylinux', [])
                run.assert_not_called()


class TestAmazonLinuxAlias(unittest.TestCase):
    """Amazon Linux sets ID=amzn; both ifamzn and legacy ifamazon must match."""

    def test_amzn_matches_both_directives(self):
        with _mock_distro('amzn', 'fedora'):
            plugin = _make_plugin()
            for directive in ('ifamzn', 'ifamazon', 'iffedora', 'ifanylinux'):
                with self.subTest(directive=directive), patch.object(
                    plugin, '_run_internal', return_value=True
                ) as run:
                    plugin.handle(directive, [])
                    run.assert_called_once()

    def test_legacy_amazon_id_matches_both_directives(self):
        with _mock_distro('amazon'):
            plugin = _make_plugin()
            for directive in ('ifamzn', 'ifamazon'):
                with self.subTest(directive=directive), patch.object(
                    plugin, '_run_internal', return_value=True
                ) as run:
                    plugin.handle(directive, [])
                    run.assert_called_once()


class TestCachyOS(unittest.TestCase):
    """CachyOS (ID=cachyos, ID_LIKE=arch) matches both cachyos and arch directives."""

    def test_ifcachyos_and_ifarch_match(self):
        with _mock_distro('cachyos', 'arch'):
            plugin = _make_plugin()
            for directive in ('ifcachyos', 'ifarch', 'ifanylinux'):
                with patch.object(plugin, '_run_internal', return_value=True) as run:
                    plugin.handle(directive, [])
                    run.assert_called_once()

    def test_other_platforms_do_not_match(self):
        with _mock_distro('cachyos', 'arch'):
            plugin = _make_plugin()
            for directive in ('ifubuntu', 'ifmacos', 'ifwindows', 'ifanybsd'):
                with patch.object(plugin, '_run_internal', return_value=True) as run:
                    result = plugin.handle(directive, [])
                    run.assert_not_called()
                    self.assertTrue(result)


class TestIdLikeGeneral(unittest.TestCase):
    """ID_LIKE with multiple entries and derivative distros."""

    def test_multi_value_id_like_matches_all(self):
        with _mock_distro('linuxmint', 'ubuntu debian'):
            plugin = _make_plugin()
            for directive in ('iflinuxmint', 'ifubuntu', 'ifdebian', 'ifanylinux'):
                with patch.object(plugin, '_run_internal', return_value=True) as run:
                    plugin.handle(directive, [])
                    run.assert_called_once()


class TestMetaAndNegationDirectives(unittest.TestCase):
    """ifany, ifnot<platform>, typo rejection, and naming hygiene."""

    def test_ifany_and_ifnotany(self):
        for did in ('ubuntu', 'darwin', 'freebsd'):
            with _mock_distro(did):
                plugin = _make_plugin()
                with patch.object(plugin, '_run_internal', return_value=True) as run:
                    plugin.handle('ifany', [])
                    run.assert_called_once()
                with patch.object(plugin, '_run_internal', return_value=True) as run:
                    result = plugin.handle('ifnotany', [])
                    run.assert_not_called()
                    self.assertTrue(result)

    def test_negation_across_platforms_and_id_like(self):
        plugin = _make_plugin()
        with _mock_distro('linuxmint', 'ubuntu debian'):
            for skipped in ('ifnotlinuxmint', 'ifnotubuntu', 'ifnotdebian', 'ifnotanylinux'):
                with patch.object(plugin, '_run_internal', return_value=True) as run:
                    plugin.handle(skipped, [])
                    run.assert_not_called()
            for matched in ('ifnotmacos', 'ifnotwindows', 'ifnotarch', 'ifnotanybsd'):
                with patch.object(plugin, '_run_internal', return_value=True) as run:
                    plugin.handle(matched, [])
                    run.assert_called_once()

    def test_typos_and_unknown_directives_rejected(self):
        plugin = _make_plugin()
        for bad in ('ifubunto', 'ifnotubunto', 'if', 'ifnot'):
            self.assertFalse(plugin.can_handle(bad))
            with self.assertRaises(ValueError):
                plugin.handle(bad, [])

    def test_no_target_starts_with_not(self):
        for target in IfPlatform._distros:
            self.assertFalse(
                target.startswith('not'),
                f"Target '{target}' starts with 'not' and would collide with 'ifnot*'",
            )


class TestWSLDetection(unittest.TestCase):
    """WSL is additive on Linux and never leaks into non-Linux platforms."""

    def test_ubuntu_on_wsl_via_env(self):
        with _mock_distro('ubuntu', 'debian'), _clean_wsl_env(), patch.dict(
            os.environ, {'WSL_DISTRO_NAME': 'Ubuntu'}
        ):
            plugin = _make_plugin()
            for matched in ('ifwsl', 'ifubuntu', 'ifdebian', 'ifanylinux'):
                with patch.object(plugin, '_run_internal', return_value=True) as run:
                    plugin.handle(matched, [])
                    run.assert_called_once()
            for skipped in ('ifnotwsl', 'ifwindows'):
                with patch.object(plugin, '_run_internal', return_value=True) as run:
                    plugin.handle(skipped, [])
                    run.assert_not_called()

    def test_arch_on_wsl_via_kernel_release(self):
        with _mock_distro('arch'), _clean_wsl_env(), patch(
            'ifplatform.platform.release', return_value='5.15.153.1-microsoft-standard-WSL2'
        ):
            plugin = _make_plugin()
            with patch.object(plugin, '_run_internal', return_value=True) as run:
                plugin.handle('ifwsl', [])
                run.assert_called_once()

    def test_native_linux_is_not_wsl(self):
        with _mock_distro('ubuntu', 'debian'), _clean_wsl_env():
            plugin = _make_plugin()
            with patch.object(plugin, '_run_internal', return_value=True) as run:
                plugin.handle('ifwsl', [])
                run.assert_not_called()
            with patch.object(plugin, '_run_internal', return_value=True) as run:
                plugin.handle('ifnotwsl', [])
                run.assert_called_once()

    def test_macos_ignores_stray_wsl_env(self):
        with _mock_distro('darwin'), patch.dict(os.environ, {'WSL_DISTRO_NAME': 'Ubuntu'}):
            plugin = _make_plugin()
            with patch.object(plugin, '_run_internal', return_value=True) as run:
                plugin.handle('ifwsl', [])
                run.assert_not_called()


class TestStdlibFallback(unittest.TestCase):
    """Zero-dependency fallback works when lib/distro submodule is absent."""

    def test_parse_os_release_lines(self):
        parsed = _parse_os_release_lines([
            '# Comment line\n',
            '\n',
            'NAME="Pop!_OS"\n',
            'ID=pop\n',
            'ID_LIKE="ubuntu debian"\n',
            "PRETTY_NAME='Pop!_OS 24.04 LTS'\n",
        ])
        self.assertEqual(parsed['ID'], 'pop')
        self.assertEqual(parsed['ID_LIKE'], 'ubuntu debian')
        self.assertEqual(parsed['PRETTY_NAME'], 'Pop!_OS 24.04 LTS')

    def test_linux_via_freedesktop_os_release(self):
        fake_info = {'ID': 'pop', 'ID_LIKE': 'ubuntu debian'}
        with patch.object(ifplatform, 'distro', None), patch(
            'ifplatform.sys.platform', 'linux'
        ), patch(
            'ifplatform.platform.freedesktop_os_release', return_value=fake_info, create=True
        ):
            plugin = _make_plugin()
            for directive in ('ifpop', 'ifubuntu', 'ifdebian', 'ifanylinux'):
                with patch.object(plugin, '_run_internal', return_value=True) as run:
                    plugin.handle(directive, [])
                    run.assert_called_once()

    def test_linux_file_fallback_and_id_normalization(self):
        os_release_text = 'ID="ol"\nID_LIKE="fedora"\n'
        with patch.object(ifplatform, 'distro', None), patch(
            'ifplatform.sys.platform', 'linux'
        ), patch(
            'ifplatform.platform.freedesktop_os_release', side_effect=OSError, create=True
        ), patch(
            'builtins.open', side_effect=lambda *a, **kw: io.StringIO(os_release_text)
        ):
            plugin = _make_plugin()
            for directive in ('iforacle', 'iffedora', 'ifanylinux'):
                with patch.object(plugin, '_run_internal', return_value=True) as run:
                    plugin.handle(directive, [])
                    run.assert_called_once()

    def test_opensuse_leap_normalization_in_fallback(self):
        fake_info = {'ID': 'opensuse-leap', 'ID_LIKE': 'suse opensuse'}
        with patch.object(ifplatform, 'distro', None), patch(
            'ifplatform.sys.platform', 'linux'
        ), patch(
            'ifplatform.platform.freedesktop_os_release', return_value=fake_info, create=True
        ):
            plugin = _make_plugin()
            with patch.object(plugin, '_run_internal', return_value=True) as run:
                plugin.handle('ifopensuse', [])
                run.assert_called_once()

    def test_macos_fallback(self):
        with patch.object(ifplatform, 'distro', None), patch(
            'ifplatform.sys.platform', 'darwin'
        ), patch('ifplatform.os.name', 'posix'), patch(
            'ifplatform.platform.system', return_value='Darwin'
        ):
            plugin = _make_plugin()
            with patch.object(plugin, '_run_internal', return_value=True) as run:
                plugin.handle('ifmacos', [])
                run.assert_called_once()
            with patch.object(plugin, '_run_internal', return_value=True) as run:
                plugin.handle('ifanylinux', [])
                run.assert_not_called()

    def test_windows_fallback(self):
        with patch.object(ifplatform, 'distro', None), patch(
            'ifplatform.sys.platform', 'win32'
        ), patch('ifplatform.os.name', 'nt'), patch(
            'ifplatform.platform.system', return_value='Windows'
        ):
            plugin = _make_plugin()
            with patch.object(plugin, '_run_internal', return_value=True) as run:
                plugin.handle('ifwindows', [])
                run.assert_called_once()
            with patch.object(plugin, '_run_internal', return_value=True) as run:
                plugin.handle('ifanylinux', [])
                run.assert_not_called()

    def test_freebsd_fallback(self):
        with patch.object(ifplatform, 'distro', None), patch(
            'ifplatform.sys.platform', 'freebsd14'
        ), patch('ifplatform.os.name', 'posix'), patch(
            'ifplatform.platform.system', return_value='FreeBSD'
        ):
            plugin = _make_plugin()
            for directive in ('iffreebsd', 'ifanybsd'):
                with patch.object(plugin, '_run_internal', return_value=True) as run:
                    plugin.handle(directive, [])
                    run.assert_called_once()
            with patch.object(plugin, '_run_internal', return_value=True) as run:
                plugin.handle('ifanylinux', [])
                run.assert_not_called()


class TestDispatcherIntegration(unittest.TestCase):
    """Inner Dispatcher inherits plugins, defaults, exit_on_failure, and dry-run."""

    def test_supports_dry_run_enabled(self):
        self.assertTrue(IfPlatform.supports_dry_run)

    def test_inherits_context_plugins_without_reloading(self):
        sentinel_plugins = [object(), object()]
        plugin = _make_plugin(with_context_plugins=True, context_plugins=sentinel_plugins)
        mock_disp = MagicMock()
        mock_disp.dispatch.return_value = True
        with patch('ifplatform.Dispatcher', return_value=mock_disp) as disp_cls, patch.object(
            ifplatform.module, 'load'
        ) as mod_load:
            self.assertTrue(plugin._run_internal([{'shell': ['true']}]))
            mod_load.assert_not_called()
            disp_cls.assert_called_once()
            self.assertEqual(disp_cls.call_args.kwargs['plugins'], sentinel_plugins)

    def test_falls_back_to_load_plugins_for_older_dotbot(self):
        plugin = _make_plugin(with_context_plugins=False)
        plugin._context.options().plugins = ['/tmp/custom_a.py']
        fake_plugin_cls = type('FakePlugin', (), {})
        mock_disp = MagicMock()
        mock_disp.dispatch.return_value = True
        with patch('ifplatform.Dispatcher', return_value=mock_disp) as disp_cls, patch.object(
            ifplatform.module, 'load', return_value=[fake_plugin_cls, fake_plugin_cls]
        ) as mod_load:
            plugin._run_internal([{'shell': ['true']}])
            plugin._run_internal([{'shell': ['true']}])
            mod_load.assert_called_once()
            self.assertEqual(disp_cls.call_args.kwargs['plugins'], [fake_plugin_cls])
            self.assertEqual(plugin._context.options().plugins, ['/tmp/custom_a.py'])

    def test_propagates_defaults_and_exit_on_failure(self):
        defaults = {'link': {'relink': True, 'create': True}}
        plugin = _make_plugin(
            with_context_plugins=True,
            context_plugins=[],
            defaults=defaults,
            exit_on_failure=True,
        )
        mock_disp = MagicMock()
        mock_disp.dispatch.return_value = True
        with patch('ifplatform.Dispatcher', return_value=mock_disp) as disp_cls:
            plugin._run_internal([{'link': {'~/.vimrc': 'vimrc'}}])
            self.assertTrue(disp_cls.call_args.kwargs['exit_on_failure'])
            mock_disp._context.set_defaults.assert_called_once_with(defaults)

    def test_compatible_with_legacy_dotbot_v1_19_dispatcher_signature(self):
        calls = []

        class LegacyDispatcher:
            def __init__(self, base_directory, only=None, skip=None, options=None):
                calls.append((base_directory, only, skip, options))
                self._context = MagicMock()

            def dispatch(self, data):
                return True

        plugin = _make_plugin(
            with_context_plugins=False,
            defaults={'shell': {'stdout': True}},
            exit_on_failure=True,
        )
        with patch('ifplatform.Dispatcher', LegacyDispatcher):
            self.assertTrue(plugin._run_internal([{'shell': ['echo hi']}]))
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], '/tmp/dotfiles')


class TestDocumentationSync(unittest.TestCase):
    """README.md documents every supported platform target."""

    def test_readme_documents_all_targets(self):
        readme_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'README.md'
        )
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme = f.read()
        for target in IfPlatform._distros:
            self.assertIn(
                f'| `{target}`',
                readme,
                f"Target '{target}' is missing from the README.md table",
            )


if __name__ == '__main__':
    unittest.main()
