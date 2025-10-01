"""Tests for gbp-webhook cli"""

# pylint: disable=missing-docstring,unused-argument

import argparse
import io
import unittest
from contextlib import redirect_stdout
from typing import Any, Callable
from unittest import mock

import gbp_testkit.fixtures as testkit
from unittest_fixtures import FixtureContext, Fixtures, fixture, given, where

from gbp_webhook import cli

type Actions = dict[str, Callable[[argparse.Namespace], Any]]


@fixture()
def cli_actions(
    _: Fixtures,
    cli_actions: Actions | None = None,  # pylint: disable=redefined-outer-name
) -> FixtureContext[mock.Mock]:
    with mock.patch.dict(cli.ACTIONS, cli_actions or {}) as mock_obj:
        yield mock_obj


@fixture()
def parser_fixture(_: Fixtures) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    cli.parse_args(parser)

    return parser


@given(cli_actions, parser_fixture, testkit.gbpcli)
@where(cli_actions={"serve": mock.Mock()})
class HandlerTests(unittest.TestCase):
    def test(self, fixtures: Fixtures) -> None:
        fixtures.gbpcli("gbp webhook serve -p 6000 --allow 1.2.3.4")

        args = fixtures.cli_actions["serve"].call_args[0][0]
        self.assertEqual(args.action, "serve")
        self.assertEqual(args.port, 6000)
        self.assertEqual(args.allow, ["1.2.3.4"])

    def test_list_plugins(self, fixtures: Fixtures) -> None:
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            status = fixtures.gbpcli("gbp webhook list-plugins")

        self.assertEqual(0, status)
        self.assertEqual("gbp_webhook.handlers:postpull\n", stdout.getvalue())
