"""tests for gbp_webhook.utils"""

# pylint: disable=missing-docstring,duplicate-code
import argparse
import os
import pathlib
import signal
import unittest
from typing import Callable
from unittest import mock

import gbp_testkit.fixtures as testkit
from unittest_fixtures import Fixtures, fixture, given

from gbp_webhook import cli, utils
from gbp_webhook.types import NGINX_CONF

TESTDIR = pathlib.Path(__file__).parent
patch = mock.patch


@fixture(testkit.tmpdir, testkit.environ)
def user_config(fixtures: Fixtures, filename: str = "config.toml") -> str:
    config_path = f"{fixtures.tmpdir}/{filename}"
    os.environ["GBPCLI_CONFIG"] = config_path

    return config_path


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


class GetCommandPathTests(unittest.TestCase):
    def test_argv0(self) -> None:
        path = utils.get_command_path(["/usr/local/bin/gbp", "webhook", "serve"])

        self.assertEqual("/usr/local/bin/gbp", path)

    @patch.dict(utils.sys.modules, {"__main__": mock.Mock(__file__="/sbin/gbp")})
    def test_argv1_does_not_start_with_slash(self) -> None:
        path = utils.get_command_path(["gbp", "webhook", "serve"])

        self.assertEqual("/sbin/gbp", path)

    @patch.dict(utils.sys.modules, {"__main__": mock.Mock()})
    def test_main_has_no_dunder_file(self) -> None:
        with self.assertRaises(RuntimeError):
            utils.get_command_path(["gbp", "webhook", "serve"])


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


class RemoveFromLstTests(unittest.TestCase):
    def test(self) -> None:
        lst = [
            "webhook",
            "install",
            "--nginx",
            "/usr/local/bin/nginx",
            "--allow",
            "10.10.10.0/24",
            "fe80::/10",
        ]

        args = utils.remove_from_lst(lst, ["webhook", "install"])

        self.assertEqual(
            [
                "--nginx",
                "/usr/local/bin/nginx",
                "--allow",
                "10.10.10.0/24",
                "fe80::/10",
            ],
            args,
        )

    def test_list_does_not_contain_item(self) -> None:
        args = utils.remove_from_lst(["gbp", "ls", "babette"], ["webhook", "install"])

        self.assertEqual(["gbp", "ls", "babette"], args)


@given(user_config)
class BuildURLTests(unittest.TestCase):
    def test(self, fixtures: Fixtures) -> None:
        with open(fixtures.user_config, "w", encoding="utf8") as fp:
            fp.write('[gbpcli]\nurl = "http://gbp.invalid/"\n')

        url = utils.build_url("git", "281")

        self.assertEqual(url, "http://gbp.invalid/machines/git/builds/281/")
