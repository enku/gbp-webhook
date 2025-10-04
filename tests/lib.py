# pylint: disable=missing-docstring,redefined-outer-name
from pathlib import Path
from typing import Any
from unittest import mock

import gbp_testkit.fixtures as testkit
from flask.app import Flask as FlaskApp
from flask.testing import FlaskClient
from unittest_fixtures import FixtureContext, Fixtures, fixture

from gbp_webhook import systemd
from gbp_webhook.app import app
from gbp_webhook.types import WEBHOOK_CONF


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


@fixture(testkit.tmpdir)
def home(fixtures: Fixtures, target: Any = systemd.Path) -> FixtureContext[Path]:
    with mock.patch.object(target, "home") as mock_obj:
        path = Path(fixtures.tmpdir, "home")
        path.mkdir()
        mock_obj.return_value = path

        yield path


@fixture()
def client(_fixtures: Fixtures, flask_app: FlaskApp = app) -> FlaskClient:
    return flask_app.test_client()
