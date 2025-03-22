"""Tests for the gbp_webhook.systemd module"""

# pylint: disable=missing-docstring
import pathlib
import tempfile
import unittest
from unittest import mock

from gbp_webhook import systemd
from gbp_webhook.types import WEBHOOK_CONF

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


@patch.object(systemd.sys, "argv", new=MOCK_ARGV)
@patch.object(systemd, "get_unit_dir")
@patch.object(systemd, "get_config_path")
class InstallTests(unittest.TestCase):
    def test_without_config_file_existing(
        self, get_config_path: Mock, get_unit_dir: Mock
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path, unit_dir = self.configure_paths(tmpdir)
            get_config_path.return_value = config_path
            get_unit_dir.return_value = unit_dir

            systemd.install(Mock())

            self.assertTrue(config_path.read_bytes().startswith(b"GBP_WEBHOOK_ARGS="))

            unit = unit_dir / "gbp-webhook.service"
            self.assertTrue(unit.exists())

    def test_with_config_file_existing(
        self, get_config_path: Mock, get_unit_dir: Mock
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path, unit_dir = self.configure_paths(tmpdir)
            get_config_path.return_value = config_path
            config_path.parent.mkdir()
            config_path.write_bytes(b"this is a test")
            get_unit_dir.return_value = unit_dir

            systemd.install(Mock())

            self.assertEqual(b"this is a test", config_path.read_bytes())

            unit = unit_dir / "gbp-webhook.service"
            self.assertTrue(unit.exists())

    def configure_paths(self, tmpdir) -> tuple[Path, Path]:
        tmp_path = Path(tmpdir)
        config_path = tmp_path.joinpath(".config", WEBHOOK_CONF)
        unit_dir = tmp_path / "unitz"

        return config_path, unit_dir


@patch.object(systemd, "get_unit_dir")
class UninstallTests(unittest.TestCase):
    def test(self, get_unit_dir: Mock) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            get_unit_dir.return_value = tmppath
            unit = tmppath.joinpath("gbp-webhook.service")
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
