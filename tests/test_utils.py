"""tests for gbp_webhook.utils"""

# pylint: disable=missing-docstring,duplicate-code
import argparse
import os
import pathlib
import signal
import unittest
from typing import Callable
from unittest import mock

from unittest_fixtures import Fixtures, given, where

from gbp_webhook import cli, utils
from gbp_webhook.types import NGINX_CONF

from . import lib

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


@given(lib.argv)
@where(argv=[])
class GetCommandPathTests(unittest.TestCase):
    def test_argv0(self, fixtures: Fixtures) -> None:
        fixtures.argv.extend(["/usr/local/bin/gbp", "webhook", "serve"])

        path = utils.get_command_path()

        self.assertEqual("/usr/local/bin/gbp", path)

    @patch.dict(utils.sys.modules, {"__main__": mock.Mock(__file__="/sbin/gbp")})
    def test_argv1_does_not_start_with_slash(self, fixtures: Fixtures) -> None:
        fixtures.argv.extend(["gbp", "webhook", "serve"])

        path = utils.get_command_path()

        self.assertEqual("/sbin/gbp", path)

    @patch.dict(utils.sys.modules, {"__main__": mock.Mock()})
    def test_main_has_no_dunder_file(self, fixtures: Fixtures) -> None:
        fixtures.argv.extend(["gbp", "webhook", "serve"])

        with self.assertRaises(RuntimeError):
            utils.get_command_path()


@patch.object(utils.sp, "Popen")
class ChildProcessTests(unittest.TestCase):
    def test(self, popen: mock.Mock) -> None:
        original_handlers = (
            signal.getsignal(signal.SIGINT),
            signal.getsignal(signal.SIGTERM),
        )
        with utils.ChildProcess() as children:
            children.add("echo", "hello world")

            popen.assert_called_once_with(("echo", "hello world"))
            process = popen.return_value
            process.wait.assert_not_called()

        process.wait.assert_called_once_with()
        process.kill.assert_not_called()

        self.assertEqual(
            original_handlers,
            (signal.getsignal(signal.SIGINT), signal.getsignal(signal.SIGTERM)),
        )

    def test_when_signal_sent(self, popen: mock.Mock) -> None:
        for signalnum in (signal.SIGINT, signal.SIGTERM):
            with self.subTest(signalnum=signalnum):
                popen.reset_mock()
                process = popen.return_value
                process.wait.side_effect = self.create_side_effect(signalnum)

                with self.assertRaises(SystemExit):
                    with utils.ChildProcess() as children:
                        children.add(["echo", "hello world"])

                    popen.assert_called_once_with(["echo", "hello world"])
                    process = popen.return_value
                    process.wait.assert_not_called()

                process.wait.assert_called_once_with()
                process.kill.assert_called_once_with()

    @staticmethod
    def create_side_effect(signalnum: int) -> Callable[[], None]:
        return lambda: os.kill(os.getpid(), signalnum)
