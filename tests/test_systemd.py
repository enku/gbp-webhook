"""Tests for the gbp_webhook.systemd module"""

# pylint: disable=missing-docstring,unused-argument
import os
import pathlib
import unittest
from unittest import mock

import gbp_testkit.fixtures as testkit
from unittest_fixtures import Fixtures, Param, given, where

from gbp_webhook import systemd
from gbp_webhook.types import WEBHOOK_CONF

from . import lib

Mock = mock.Mock
Path = pathlib.Path

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


@given(get_config_path=testkit.patch)
@given(lib.unit_dir, lib.config_path, argv=testkit.patch, get_unit_dir=testkit.patch)
@where(get_unit_dir__target="gbp_webhook.systemd.get_unit_dir")
@where(get_unit_dir__return_value=Param(lambda fixtures: fixtures.unit_dir))
@where(get_config_path__target="gbp_webhook.systemd.get_config_path")
@where(get_config_path__return_value=Param(lambda fixtures: fixtures.config_path))
@where(argv__target="sys.argv")
@where(argv__new=MOCK_ARGV)
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


@given(lib.config_path, argv=testkit.patch, get_config_path=testkit.patch)
@where(get_config_path__target="gbp_webhook.systemd.get_config_path")
@where(get_config_path__return_value=Param(lambda fixtures: fixtures.config_path))
@where(argv__target="sys.argv")
@where(argv__new=MOCK_ARGV)
class InstallConfigTests(unittest.TestCase):
    def test(self, fixtures: Fixtures) -> None:
        config_path = systemd.get_config_path()

        systemd.install_config(config_path)

        self.assertTrue(config_path.is_file())
        content = config_path.read_text("UTF-8")
        self.assertEqual(
            content,
            "GBP_WEBHOOK_ARGS='--nginx /usr/local/bin/nginx --allow 10.10.10.0/24 fe80::/10'",
        )


@given(lib.unit_dir, get_unit_dir=testkit.patch)
@where(get_unit_dir__target="gbp_webhook.systemd.get_unit_dir")
@where(get_unit_dir__return_value=Param(lambda fixtures: fixtures.unit_dir))
class UninstallTests(unittest.TestCase):
    def test(self, fixtures: Fixtures) -> None:
        unit = systemd.get_unit_dir().joinpath("gbp-webhook.service")
        unit.touch()

        systemd.uninstall(Mock())

        self.assertFalse(unit.exists())


@given(lib.home, testkit.environ)
class GetUnitDirTests(unittest.TestCase):
    def test_without_xdg_data_home(self, fixtures: Fixtures) -> None:
        path = systemd.get_unit_dir()
        home = fixtures.home

        self.assertEqual(home.joinpath(".local/share/systemd/user"), path)

    def test_with_xdg_data_home(self, fixtures: Fixtures) -> None:
        os.environ["XDG_DATA_HOME"] = "/path/to/ruin"

        path = systemd.get_unit_dir()

        self.assertEqual(Path("/path/to/ruin/.local/share/systemd/user"), path)


@given(lib.home)
class GetConfigPathTests(unittest.TestCase):
    def test(self, fixtures: Fixtures) -> None:
        config_path = systemd.get_config_path()
        home = fixtures.home

        self.assertEqual(home.joinpath(f".config/{WEBHOOK_CONF}"), config_path)
