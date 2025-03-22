"""Tests for gbp-webhook cli"""

# pylint: disable=missing-docstring

import argparse
import unittest
from unittest import mock

from gbp_webhook import cli

patch = mock.patch


@patch.dict(cli.ACTIONS, {"serve": mock.Mock()})
class HanderTests(unittest.TestCase):
    def test(self) -> None:
        parser = argparse.ArgumentParser()
        cli.parse_args(parser)
        args = parser.parse_args(["-p", "6000", "serve", "--allow", "0.0.0.0"])

        cli.handler(args, mock.Mock(), mock.Mock())

        cli.ACTIONS["serve"].assert_called_once_with(args)


class ParseArgsTests(unittest.TestCase):
    def test(self) -> None:
        parser = argparse.ArgumentParser()
        cli.parse_args(parser)
