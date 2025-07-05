"""Tests for the gbp_webhook.systemd module"""

# pylint: disable=missing-docstring,unused-argument
import pathlib
import unittest
from unittest import mock

from unittest_fixtures import Fixtures, given, where

from gbp_webhook import systemd
from gbp_webhook.types import WEBHOOK_CONF

from . import lib

Mock = mock.Mock
Path = pathlib.Path
patch = mock.patch

MOCK_ARGV = [
    "gbp",
    "webhook",
    "install",
    "--nginx",
    "/usr/local/bin/nginx",
    "--allow",
    "10.10.10.0/24",
    "fe80::/10",
]


@given(lib.get_unit_dir, lib.get_config_path, lib.argv)
@where(argv=MOCK_ARGV)
class InstallTests(unittest.TestCase):
    def test_without_config_file_existing(self, fixtures: Fixtures) -> None:
        config_path = systemd.get_config_path()
        systemd.install(Mock())

        self.assertTrue(config_path.read_bytes().startswith(b"GBP_WEBHOOK_ARGS="))

        unit = systemd.get_unit_dir().joinpath("gbp-webhook.service")
        self.assertTrue(unit.exists())

    def test_with_config_file_existing(self, fixtures: Fixtures) -> None:
        config_path = systemd.get_config_path()
        config_path.write_bytes(b"this is a test")

        systemd.install(Mock())

        self.assertEqual(b"this is a test", config_path.read_bytes())

        unit = systemd.get_unit_dir().joinpath("gbp-webhook.service")
        self.assertTrue(unit.exists())


@given(lib.get_unit_dir)
class UninstallTests(unittest.TestCase):
    def test(self, fixtures: Fixtures) -> None:
        unit = systemd.get_unit_dir().joinpath("gbp-webhook.service")
        unit.touch()

        systemd.uninstall(Mock())

        self.assertFalse(unit.exists())


@patch.dict(systemd.os.environ, {}, clear=True)
class GetUnitDirTests(unittest.TestCase):
    @patch.object(systemd.Path, "home")
    def test_without_xdg_data_home(self, home: Mock) -> None:
        home.return_value = Path("/blah/blah")

        path = systemd.get_unit_dir()

        self.assertEqual(Path("/blah/blah/.local/share/systemd/user"), path)

    def test_with_xdg_data_home(self) -> None:
        systemd.os.environ["XDG_DATA_HOME"] = "/path/to/ruin"

        path = systemd.get_unit_dir()

        self.assertEqual(Path("/path/to/ruin/.local/share/systemd/user"), path)


@patch.object(systemd.Path, "home")
class GetConfigPathTests(unittest.TestCase):
    def test(self, home: Mock) -> None:
        home.return_value = Path("/path/to/ruin")

        config_path = systemd.get_config_path()

        self.assertEqual(Path(f"/path/to/ruin/.config/{WEBHOOK_CONF}"), config_path)


class ArgsFromArgvTests(unittest.TestCase):
    def test(self) -> None:
        args = systemd.args_from_argv(MOCK_ARGV)

        self.assertEqual(
            "--nginx /usr/local/bin/nginx --allow 10.10.10.0/24 fe80::/10", args
        )
