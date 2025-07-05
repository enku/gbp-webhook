"""Tests for gbp-webhook cli"""

# pylint: disable=missing-docstring

import argparse
import unittest
from typing import Any, Callable, TypeAlias
from unittest import mock

from unittest_fixtures import FixtureContext, Fixtures, fixture, given, where

from gbp_webhook import cli

Actions: TypeAlias = dict[str, Callable[[argparse.Namespace], Any]]


@fixture()
def cli_actions(
    _: Fixtures,
    cli_actions: Actions | None = None,  # pylint: disable=redefined-outer-name
) -> FixtureContext[mock.Mock]:
    with mock.patch.dict(cli.ACTIONS, cli_actions or {}) as mock_obj:
        yield mock_obj


@given(cli_actions)
@where(cli_actions={"serve": mock.Mock()})
class HanderTests(unittest.TestCase):
    def test(self, fixtures: Fixtures) -> None:
        parser = argparse.ArgumentParser()
        cli.parse_args(parser)
        args = parser.parse_args(["-p", "6000", "serve", "--allow", "0.0.0.0"])

        cli.handler(args, mock.Mock(), mock.Mock())

        actions = fixtures.cli_actions
        actions["serve"].assert_called_once_with(args)


class ParseArgsTests(unittest.TestCase):
    def test(self) -> None:
        parser = argparse.ArgumentParser()
        cli.parse_args(parser)
