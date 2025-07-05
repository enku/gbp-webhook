# pylint: disable=missing-docstring
import tempfile
from pathlib import Path
from types import ModuleType as Module
from unittest import mock

from unittest_fixtures import FixtureContext, Fixtures, fixture

from gbp_webhook import app, server
from gbp_webhook.types import WEBHOOK_CONF

FC = FixtureContext
Mock = mock.Mock


@fixture()
def pre_shared_key(_: Fixtures, target: Module = app, key: str = "key") -> FC[str]:
    with mock.patch.object(target, "PRE_SHARED_KEY", key):
        yield key


@fixture()
def executor(_: Fixtures, target: Module = app) -> FC[Mock]:
    with mock.patch.object(target, "executor") as mock_obj:
        yield mock_obj


@fixture()
def add_process(_: Fixtures) -> FC[Mock]:
    with mock.patch.object(server.ChildProcess, "add") as mock_obj:
        yield mock_obj


@fixture()
def tmpdir(_: Fixtures) -> FC[str]:
    with tempfile.TemporaryDirectory() as _tmpdir:
        yield _tmpdir


@fixture(tmpdir)
def unit_dir(fixtures: Fixtures, name: str = "unitz", create: bool = True) -> Path:
    path = Path(fixtures.tmpdir, name)

    if create:
        path.mkdir()

    return Path(fixtures.tmpdir, name)


@fixture(tmpdir)
def config_path(fixtures: Fixtures, create: bool = True) -> Path:
    path = Path(fixtures.tmpdir, ".config", WEBHOOK_CONF)

    if create:
        path.parent.mkdir()

    return path
