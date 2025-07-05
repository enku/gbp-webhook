"""Tests for the gbp-webhook server"""

# pylint: disable=missing-docstring
import argparse
import os
import signal
import sys
import unittest
from typing import Any
from unittest import mock

from unittest_fixtures import Fixtures, given

from gbp_webhook import cli, server
from gbp_webhook.types import NGINX_CONF

from . import lib

Mock = mock.Mock


@given(lib.add_process)
class ServeTests(unittest.TestCase):
    # pylint: disable=protected-access
    parser = argparse.ArgumentParser()
    cli.parse_args(parser)
    args = parser.parse_args(
        [
            "serve",
            "--allow",
            "0.0.0.0",
            "--ssl",
            "--ssl-cert=/path/to/my.crt",
            "--ssl-key=/path/to/my.key",
        ]
    )

    def test(self, fixtures: Fixtures) -> None:
        tmpdir = server.serve(self.args)

        gunicorn = mock.call(
            sys.executable,
            "-m",
            "gunicorn",
            "-b",
            f"unix:{tmpdir}/gunicorn.sock",
            server.APP,
        )
        nginx = mock.call(
            self.args.nginx, "-e", f"{tmpdir}/error.log", "-c", f"{tmpdir}/{NGINX_CONF}"
        )
        self.assertEqual(2, fixtures.add_process.call_count)
        fixtures.add_process.assert_has_calls([gunicorn, nginx])

    def test_ctrl_c_pressed(self, fixtures: Fixtures) -> None:
        times_called = 0

        def add_side_effect(*_args: Any) -> None:
            nonlocal times_called

            times_called += 1
            if times_called > 1:
                os.kill(os.getpid(), signal.SIGINT)

        fixtures.add_process.side_effect = add_side_effect

        with self.assertRaises(SystemExit):
            server.serve(self.args)

        self.assertEqual(2, fixtures.add_process.call_count)
        for child in fixtures.add_process.calls:
            child.kill.assert_called()
