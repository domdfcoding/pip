import importlib
import ntpath
import os
import posixpath
import sys

import pretend
import pytest
from pip._vendor import platformdirs

from pip._internal.utils import appdirs


@pytest.fixture()
def platformdirs_win32(monkeypatch):
    # Monkeypatch platformdirs to pretend we're running on Windows

    with monkeypatch.context() as m:
        m.setattr(sys, "platform", "win32")
        m.setattr(os, "path", ntpath)
        importlib.reload(platformdirs)
        importlib.reload(appdirs)
        yield

    importlib.reload(platformdirs)
    importlib.reload(appdirs)


@pytest.fixture()
def platformdirs_darwin(monkeypatch):
    # Monkeypatch platformdirs to pretend we're running on macOS
    
    with monkeypatch.context() as m:
        m.setattr(sys, "platform", "darwin")
        m.setattr(os, "path", posixpath)
        importlib.reload(platformdirs)
        importlib.reload(appdirs)
        yield

    importlib.reload(platformdirs)
    importlib.reload(appdirs)


@pytest.fixture()
def platformdirs_linux(monkeypatch):
    # Monkeypatch platformdirs to pretend we're running on Linux

    with monkeypatch.context() as m:
        m.setattr(sys, "platform", "linux")
        m.setattr(os, "path", posixpath)
        importlib.reload(platformdirs)
        importlib.reload(appdirs)
        yield

    importlib.reload(platformdirs)
    importlib.reload(appdirs)


class TestUserCacheDir:

    def test_user_cache_dir_win(self, monkeypatch, platformdirs_win32):
        @pretend.call_recorder
        def _get_win_folder(base):
            return "C:\\Users\\test\\AppData\\Local"

        monkeypatch.setattr(
            platformdirs,
            "_get_win_folder",
            _get_win_folder,
            raising=False,
        )

        assert (appdirs.user_cache_dir("pip") ==
                "C:\\Users\\test\\AppData\\Local\\pip\\Cache")
        assert _get_win_folder.calls == [pretend.call("CSIDL_LOCAL_APPDATA")]

    def test_user_cache_dir_osx(self, monkeypatch, platformdirs_darwin):
        monkeypatch.setenv("HOME", "/home/test")

        assert appdirs.user_cache_dir("pip") == "/home/test/Library/Caches/pip"

    def test_user_cache_dir_linux(self, monkeypatch, platformdirs_linux):
        monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
        monkeypatch.setenv("HOME", "/home/test")

        assert appdirs.user_cache_dir("pip") == "/home/test/.cache/pip"

    def test_user_cache_dir_linux_override(self, monkeypatch, platformdirs_linux):
        monkeypatch.setenv("XDG_CACHE_HOME", "/home/test/.other-cache")
        monkeypatch.setenv("HOME", "/home/test")

        assert appdirs.user_cache_dir("pip") == "/home/test/.other-cache/pip"

    def test_user_cache_dir_linux_home_slash(self, monkeypatch, platformdirs_linux):
        # Verify that we are not affected by https://bugs.python.org/issue14768
        monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
        monkeypatch.setenv("HOME", "/")

        assert appdirs.user_cache_dir("pip") == "/.cache/pip"

    def test_user_cache_dir_unicode(self, monkeypatch):
        if sys.platform != 'win32':
            return

        def my_get_win_folder(csidl_name):
            return "\u00DF\u00E4\u03B1\u20AC"

        monkeypatch.setattr(platformdirs, "_get_win_folder", my_get_win_folder)

        # Do not use the isinstance expression directly in the
        # assert statement, as the Unicode characters in the result
        # cause pytest to fail with an internal error on Python 2.7
        result_is_str = isinstance(appdirs.user_cache_dir('test'), str)
        assert result_is_str, "user_cache_dir did not return a str"

        # Test against regression #3463
        from pip._internal.cli.main_parser import create_main_parser
        create_main_parser().print_help()  # This should not crash


class TestSiteConfigDirs:

    def test_site_config_dirs_win(self, monkeypatch, platformdirs_win32):
        @pretend.call_recorder
        def _get_win_folder(base):
            return "C:\\ProgramData"

        monkeypatch.setattr(
            platformdirs,
            "_get_win_folder",
            _get_win_folder,
            raising=False,
        )

        assert appdirs.site_config_dirs("pip") == ["C:\\ProgramData\\pip"]
        assert _get_win_folder.calls == [pretend.call("CSIDL_COMMON_APPDATA")]

    # XXX: domdfcoding, 2021-07-25
    @pytest.mark.xfail(reason="Directory changed in platformdirs")
    def test_site_config_dirs_osx(self, monkeypatch, platformdirs_darwin):
        monkeypatch.setenv("HOME", "/home/test")

        assert appdirs.site_config_dirs("pip") == \
            ["/Library/Application Support/pip"]

    def test_site_config_dirs_linux(self, monkeypatch, platformdirs_linux):
        monkeypatch.delenv("XDG_CONFIG_DIRS", raising=False)

        assert appdirs.site_config_dirs("pip") == [
            '/etc/xdg/pip',
            '/etc'
        ]

    def test_site_config_dirs_linux_override(self, monkeypatch, platformdirs_linux):
        monkeypatch.setattr(os, "pathsep", ':')
        monkeypatch.setenv("XDG_CONFIG_DIRS", "/spam:/etc:/etc/xdg")

        assert appdirs.site_config_dirs("pip") == [
            '/spam/pip',
            '/etc/pip',
            '/etc/xdg/pip',
            '/etc'
        ]

    # XXX: domdfcoding 2021-07-25
    @pytest.mark.xfail(reason="Used to be patched by pip in appdirs.py:250")
    def test_site_config_dirs_linux_empty(self, monkeypatch, platformdirs_linux):
        monkeypatch.setattr(os, "pathsep", ':')
        monkeypatch.setenv("XDG_CONFIG_DIRS", "")
        assert appdirs.site_config_dirs("pip") == ['/etc/xdg/pip', '/etc']


class TestUserConfigDir:

    def test_user_config_dir_win_no_roaming(self, monkeypatch, platformdirs_win32):
        @pretend.call_recorder
        def _get_win_folder(base):
            return "C:\\Users\\test\\AppData\\Local"

        monkeypatch.setattr(
            platformdirs,
            "_get_win_folder",
            _get_win_folder,
            raising=False,
        )

        assert (
            appdirs.user_config_dir("pip", roaming=False) ==
            "C:\\Users\\test\\AppData\\Local\\pip"
        )
        assert _get_win_folder.calls == [pretend.call("CSIDL_LOCAL_APPDATA")]

    def test_user_config_dir_win_yes_roaming(self, monkeypatch, platformdirs_win32):
        @pretend.call_recorder
        def _get_win_folder(base):
            return "C:\\Users\\test\\AppData\\Roaming"

        monkeypatch.setattr(
            platformdirs,
            "_get_win_folder",
            _get_win_folder,
            raising=False,
        )

        assert (appdirs.user_config_dir("pip") ==
                "C:\\Users\\test\\AppData\\Roaming\\pip")
        assert _get_win_folder.calls == [pretend.call("CSIDL_APPDATA")]

    def test_user_config_dir_osx(self, monkeypatch, platformdirs_darwin):
        monkeypatch.setenv("HOME", "/home/test")

        if os.path.isdir('/home/test/Library/Application Support/'):
            assert (appdirs.user_config_dir("pip") ==
                    "/home/test/Library/Application Support/pip")
        else:
            assert (appdirs.user_config_dir("pip") ==
                    "/home/test/.config/pip")

    def test_user_config_dir_linux(self, monkeypatch, platformdirs_darwin):
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        monkeypatch.setenv("HOME", "/home/test")

        assert appdirs.user_config_dir("pip") == "/home/test/.config/pip"

    def test_user_config_dir_linux_override(self, monkeypatch, platformdirs_linux):
        monkeypatch.setenv("XDG_CONFIG_HOME", "/home/test/.other-config")
        monkeypatch.setenv("HOME", "/home/test")

        assert appdirs.user_config_dir("pip") == "/home/test/.other-config/pip"

    def test_user_config_dir_linux_home_slash(self, monkeypatch, platformdirs_linux):
        # Verify that we are not affected by https://bugs.python.org/issue14768
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        monkeypatch.setenv("HOME", "/")

        assert appdirs.user_config_dir("pip") == "/.config/pip"
