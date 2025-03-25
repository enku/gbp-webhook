"""tests for gbp_webhook.utils"""

# pylint: disable=missing-docstring,duplicate-code
import argparse
import os
import pathlib
import signal
import unittest
from unittest import mock

from gbp_webhook import cli, utils
from gbp_webhook.types import NGINX_CONF

TESTDIR = pathlib.Path(__file__).parent
patch = mock.patch


class RenderTemplateTests(unittest.TestCase):
    maxDiff = None

    def test(self) -> None:
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

        result = utils.render_template(NGINX_CONF, home="/test/home", options=args)

        expected = TESTDIR.joinpath(NGINX_CONF).read_text("ascii")
        self.assertEqual(expected, result)


@patch.object(utils.sys, "argv", new_callable=list)
class GetCommandPathTests(unittest.TestCase):
    def test_argv0(self, argv: list[str]) -> None:
        argv.extend(["/usr/local/bin/gbp", "webhook", "serve"])

        path = utils.get_command_path()

        self.assertEqual("/usr/local/bin/gbp", path)

    @patch.dict(utils.sys.modules, {"__main__": mock.Mock(__file__="/sbin/gbp")})
    def test_argv1_does_not_start_with_slash(self, argv: list[str]) -> None:
        argv.extend(["gbp", "webhook", "serve"])

        path = utils.get_command_path()

        self.assertEqual("/sbin/gbp", path)

    @patch.dict(utils.sys.modules, {"__main__": mock.Mock()})
    def test_main_has_no_dunder_file(self, argv: list[str]) -> None:
        argv.extend(["gbp", "webhook", "serve"])

        with self.assertRaises(RuntimeError):
            utils.get_command_path()


class RegisterSignalHandlerTests(unittest.TestCase):
    def test(self) -> None:
        orig_handler = signal.getsignal(signal.SIGUSR1)
        callback = mock.Mock()

        @utils.register_signal_handler(signal.SIGUSR1, callback)
        def fun():
            os.kill(os.getpid(), signal.SIGUSR1)

        fun()

        callback.assert_called_once_with(signal.SIGUSR1, mock.ANY)
        self.assertEqual(orig_handler, signal.getsignal(signal.SIGUSR1))
