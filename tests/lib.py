# pylint: disable=missing-docstring
from types import ModuleType as Module
from unittest import mock

from unittest_fixtures import FixtureContext, Fixtures, fixture

from gbp_webhook import app

FC = FixtureContext


@fixture()
def pre_shared_key(_: Fixtures, target: Module = app, key: str = "key") -> FC[str]:
    with mock.patch.object(target, "PRE_SHARED_KEY", key):
        yield key
