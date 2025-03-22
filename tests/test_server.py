"""Tests for the gbp-webhook server"""

# pylint: disable=missing-docstring
import argparse
import signal
import sys
import unittest
from unittest import mock

from gbp_webhook import cli, server
from gbp_webhook.types import NGINX_CONF

Mock = mock.Mock
patch = mock.patch


@patch.object(server.utils, "start_process")
@patch.object(server, "_CHILDREN", new_callable=list)
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

    def test(self, children: list[Mock], start_process: Mock) -> None:
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
        start_process.assert_has_calls([gunicorn, nginx, gunicorn.wait(), nginx.wait()])

        self.assertEqual(2, len(children))

    def test_ctrl_c_pressed(self, children: list[Mock], start_process: Mock) -> None:
        interruped = Mock()
        interruped.wait.side_effect = KeyboardInterrupt
        start_process.side_effect = (Mock(), interruped)

        with self.assertRaises(SystemExit):
            server.serve(self.args)

        self.assertEqual(2, len(children))
        for child in children:
            child.kill.assert_called()


class ShutdownTests(unittest.TestCase):
    def test(self) -> None:
        mock_children = [Mock(), Mock()]

        with patch.object(server, "_CHILDREN", new=mock_children):
            with self.assertRaises(SystemExit):
                server.shutdown(signal.SIGTERM, None)

        for child in mock_children:
            child.kill.assert_called_once_with()
