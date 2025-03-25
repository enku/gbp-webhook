"""Tests for the gbp-webhook server"""

# pylint: disable=missing-docstring
import argparse
import os
import signal
import sys
import unittest
from typing import Any
from unittest import mock

from gbp_webhook import cli, server
from gbp_webhook.types import NGINX_CONF

Mock = mock.Mock
patch = mock.patch


@patch.object(server.utils.ChildProcess, "add")
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

    def test(self, add_process: Mock) -> None:
        tmpdir = server.serve(self.args)

        gunicorn = mock.call(
            [
                sys.executable,
                "-m",
                "gunicorn",
                "-b",
                f"unix:{tmpdir}/gunicorn.sock",
                server.APP,
            ]
        )
        nginx = mock.call(
            [
                self.args.nginx,
                "-e",
                f"{tmpdir}/error.log",
                "-c",
                f"{tmpdir}/{NGINX_CONF}",
            ]
        )
        self.assertEqual(2, add_process.call_count)
        add_process.assert_has_calls([gunicorn, nginx])

    def test_ctrl_c_pressed(self, add_process: Mock) -> None:
        times_called = 0

        def add_side_effect(_args: Any) -> None:
            nonlocal times_called

            times_called += 1
            if times_called > 1:
                os.kill(os.getpid(), signal.SIGINT)

        add_process.side_effect = add_side_effect

        with self.assertRaises(SystemExit):
            server.serve(self.args)

        self.assertEqual(2, add_process.call_count)
        for child in add_process.calls:
            child.kill.assert_called()


class ShutdownTests(unittest.TestCase):
    def test(self) -> None:
        with self.assertRaises(SystemExit):
            server.shutdown(signal.SIGTERM, None)
