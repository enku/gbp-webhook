# pylint: disable=missing-docstring,redefined-outer-name
import os
import sys
from pathlib import Path
from types import ModuleType as Module
from typing import Any, Sequence
from unittest import mock

import gbp_testkit.fixtures as testkit
from unittest_fixtures import FixtureContext, Fixtures, fixture

from gbp_webhook import systemd
from gbp_webhook.types import WEBHOOK_CONF

FC = FixtureContext
Mock = mock.Mock


@fixture(testkit.tmpdir)
def unit_dir(fixtures: Fixtures, name: str = "unitz", create: bool = True) -> Path:
    path = Path(fixtures.tmpdir, name)

    if create:
        path.mkdir()

    return path


@fixture(testkit.tmpdir)
def config_path(fixtures: Fixtures, create: bool = True) -> Path:
    path = Path(fixtures.tmpdir, ".config", WEBHOOK_CONF)

    if create:
        path.parent.mkdir()

    return path


@fixture(unit_dir)
def get_unit_dir(fixtures: Fixtures, target: Module = systemd) -> FC[Mock]:
    with mock.patch.object(target, "get_unit_dir") as mock_obj:
        mock_obj.return_value = fixtures.unit_dir
        yield mock_obj


@fixture(config_path)
def get_config_path(fixtures: Fixtures, target: Module = systemd) -> FC[Mock]:
    with mock.patch.object(target, "get_config_path") as mock_obj:
        mock_obj.return_value = fixtures.config_path
        yield mock_obj


@fixture()
def argv(_: Fixtures, argv: Sequence[str] | None = None) -> FC[list[str]]:
    argv = ["gbp", "webhook", "serve"] if argv is None else list(argv)

    with mock.patch.object(sys, "argv", new=argv):
        yield argv


@fixture(testkit.tmpdir)
def home(fixtures: Fixtures, target: Any = systemd.Path) -> FC[Path]:
    with mock.patch.object(target, "home") as mock_obj:
        path = Path(fixtures.tmpdir, "home")
        path.mkdir()
        mock_obj.return_value = path

        yield path


@fixture()
def environ(
    _: Fixtures, clear: bool = True, environ: dict[str, str] | None = None
) -> FC[None]:
    with mock.patch.dict(os.environ, environ or {}, clear=clear):
        yield
