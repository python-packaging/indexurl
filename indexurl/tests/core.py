import os
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from ..core import (
    _get_global_index_url_from_file,
    _get_possible_config_locations,
    get_index_url,
)


@contextmanager
def patch_env(var: str, value: str) -> Generator[None, None, None]:
    old_value = os.getenv(var)
    os.environ[var] = value
    yield
    if old_value is None:
        del os.environ[var]
    else:
        os.environ[var] = old_value


class IndexUrlTest(unittest.TestCase):
    def test_basic_reading(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "a.ini")
            self.assertEqual(None, _get_global_index_url_from_file(p))
            p.write_text("")
            self.assertEqual(None, _get_global_index_url_from_file(p))
            p.write_text("[global]\n")
            self.assertEqual(None, _get_global_index_url_from_file(p))
            p.write_text("[global]\nfoo=a\n")
            self.assertEqual(None, _get_global_index_url_from_file(p))

            p.write_text("[global]\nindex-url=a")
            self.assertEqual("a", _get_global_index_url_from_file(p))
            p.write_text("[global]\nindex-url = a\n")
            self.assertEqual("a", _get_global_index_url_from_file(p))
            p.write_text("[global]\nindex-url = a\r\n")
            self.assertEqual("a", _get_global_index_url_from_file(p))
            p.write_text("]")
            self.assertEqual(None, _get_global_index_url_from_file(p))

    def test_pip_config_file(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            Path(d, "pip.conf").write_text("[global]\nindex-url=a\n")
            Path(d, "pip.t").write_text("[global]\nindex-url=t\n")
            with patch_env("PIP_CONFIG_FILE", str(Path(d, "pip.t"))), patch_env(
                "HOME", "/foo"
            ):
                self.assertEqual("t", get_index_url())
                with patch_env("VIRTUAL_ENV", d):
                    self.assertEqual("a", get_index_url())
            with patch_env("PIP_CONFIG_FILE", "os.devnull"), patch_env(
                "VIRTUAL_ENV", d
            ):
                self.assertEqual("https://pypi.org/simple", get_index_url())

    @unittest.skipIf(os.name == "nt", "xfail on windows")
    def test_virtual_env(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            Path(d, "pip.conf").write_text("[global]\nindex-url=a\n")
            with patch_env("VIRTUAL_ENV", d):
                self.assertEqual("a", get_index_url())

    # This one only makes sense on *nix
    def test_xdg_config_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            with patch_env("XDG_CONFIG_DIRS", f"{d},"), patch_env("HOME", "/foo"):
                Path(d, "pip").mkdir()
                Path(d, "pip", "pip.conf").write_text("[global]\nindex-url=a\n")
                self.assertEqual("a", get_index_url())

    def test_fallback(self) -> None:
        with patch_env("VIRTUAL_ENV", ""), patch_env("XDG_CONFIG_DIRS", ""), patch_env(
            "HOME", ""
        ), patch_env("XDG_CONFIG_HOME", ""), patch_env("PIP_CONFIG_FILE", ""):
            self.assertEqual("https://pypi.org/simple", get_index_url())

    @unittest.skipIf(os.name == "nt", "xfail on windows")
    def test_get_possible_config_locations(self) -> None:
        with patch_env("VIRTUAL_ENV", "/foo"), patch_env(
            "PIP_CONFIG_FILE", "/bar/pip.conf"
        ), patch_env("XDG_CONFIG_DIRS", "/a,/b"), patch_env("HOME", "/home2"):
            self.assertEqual(
                [
                    Path("/foo/pip.conf"),
                    Path("/home2/.config/pip/pip.conf"),
                    Path("/etc/pip.conf"),
                    Path("/a/pip/pip.conf"),
                    Path("/b/pip/pip.conf"),
                    Path("/bar/pip.conf"),
                ],
                _get_possible_config_locations(),
            )

    @unittest.skipIf(os.name == "nt", "xfail on windows")
    def test_get_possible_config_locations_devnull(self) -> None:
        with patch_env("VIRTUAL_ENV", "/foo"), patch_env(
            "PIP_CONFIG_FILE", "os.devnull"
        ), patch_env("XDG_CONFIG_DIRS", "/a,/b"), patch_env("HOME", "/home2"):
            self.assertEqual(
                [
                    Path("/foo/pip.conf"),
                    Path("/home2/.config/pip/pip.conf"),
                    Path("/etc/pip.conf"),
                    Path("/a/pip/pip.conf"),
                    Path("/b/pip/pip.conf"),
                ],
                _get_possible_config_locations(),
            )
