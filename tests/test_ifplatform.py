import sys
import os
import logging
import unittest
from unittest.mock import MagicMock, patch


# dotbot isn't installed, so mock it before ifplatform is imported
class _MockPlugin:
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
from ifplatform import IfPlatform
import distro


def _make_plugin():
    context = MagicMock()
    context.options.return_value.plugins = []
    context.options.return_value.plugin_dirs = []
    context.options.return_value.disable_built_in_plugins = True
    return IfPlatform(context)


class TestDirectMatch(unittest.TestCase):
    """Native distro IDs match their own directive."""

    @patch('distro.id', return_value='arch')
    @patch('distro.like', return_value='')
    def test_arch_matches_ifarch(self, _like, _id):
        plugin = _make_plugin()
        with patch.object(plugin, '_run_internal', return_value=True) as run:
            plugin.handle('ifarch', [])
            run.assert_called_once()

    @patch('distro.id', return_value='ubuntu')
    @patch('distro.like', return_value='debian')
    def test_ubuntu_matches_ifubuntu(self, _like, _id):
        plugin = _make_plugin()
        with patch.object(plugin, '_run_internal', return_value=True) as run:
            plugin.handle('ifubuntu', [])
            run.assert_called_once()

    @patch('distro.id', return_value='darwin')
    @patch('distro.like', return_value='')
    def test_darwin_maps_to_ifmacos(self, _like, _id):
        plugin = _make_plugin()
        with patch.object(plugin, '_run_internal', return_value=True) as run:
            plugin.handle('ifmacos', [])
            run.assert_called_once()


class TestCachyOS(unittest.TestCase):
    """CachyOS (ID=cachyos, ID_LIKE=arch) should match arch directives."""

    @patch('distro.id', return_value='cachyos')
    @patch('distro.like', return_value='arch')
    def test_ifarch_matches(self, _like, _id):
        plugin = _make_plugin()
        with patch.object(plugin, '_run_internal', return_value=True) as run:
            plugin.handle('ifarch', [])
            run.assert_called_once()

    @patch('distro.id', return_value='cachyos')
    @patch('distro.like', return_value='arch')
    def test_ifanylinux_matches(self, _like, _id):
        plugin = _make_plugin()
        with patch.object(plugin, '_run_internal', return_value=True) as run:
            plugin.handle('ifanylinux', [])
            run.assert_called_once()

    @patch('distro.id', return_value='cachyos')
    @patch('distro.like', return_value='arch')
    def test_ifubuntu_does_not_match(self, _like, _id):
        plugin = _make_plugin()
        with patch.object(plugin, '_run_internal', return_value=True) as run:
            result = plugin.handle('ifubuntu', [])
            run.assert_not_called()
            self.assertTrue(result)

    @patch('distro.id', return_value='cachyos')
    @patch('distro.like', return_value='arch')
    def test_ifmacos_does_not_match(self, _like, _id):
        plugin = _make_plugin()
        with patch.object(plugin, '_run_internal', return_value=True) as run:
            result = plugin.handle('ifmacos', [])
            run.assert_not_called()
            self.assertTrue(result)


class TestIdLikeGeneral(unittest.TestCase):
    """ID_LIKE with multiple entries and other derivative distros."""

    @patch('distro.id', return_value='linuxmint')
    @patch('distro.like', return_value='ubuntu debian')
    def test_multi_value_id_like_matches_first(self, _like, _id):
        plugin = _make_plugin()
        with patch.object(plugin, '_run_internal', return_value=True) as run:
            plugin.handle('ifubuntu', [])
            run.assert_called_once()

    @patch('distro.id', return_value='linuxmint')
    @patch('distro.like', return_value='ubuntu debian')
    def test_multi_value_id_like_matches_second(self, _like, _id):
        plugin = _make_plugin()
        with patch.object(plugin, '_run_internal', return_value=True) as run:
            plugin.handle('ifdebian', [])
            run.assert_called_once()

    @patch('distro.id', return_value='linuxmint')
    @patch('distro.like', return_value='ubuntu debian')
    def test_ifanylinux_matches_via_id_like(self, _like, _id):
        plugin = _make_plugin()
        with patch.object(plugin, '_run_internal', return_value=True) as run:
            plugin.handle('ifanylinux', [])
            run.assert_called_once()


if __name__ == '__main__':
    unittest.main()
