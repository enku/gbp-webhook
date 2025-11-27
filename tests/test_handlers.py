"""Tests for gbp-webhook handlers"""

# pylint: disable=missing-docstring,unused-argument

import unittest

import gbp_testkit.fixtures as testkit
from unittest_fixtures import Fixtures, given, where

from gbp_webhook import handlers

init_notify = handlers.init_notify


class PostPullTests(unittest.TestCase):
    def test(self) -> None:
        notify = handlers.init_notify()
        build = {"machine": "babette", "build_id": "1554"}
        event = {"name": "postpull", "machine": "babette", "data": {"build": build}}

        handlers.postpull(event)

        notify.Notification.new.assert_called_once_with(
            "babette", "babette has pushed build 1554", handlers.ICON
        )
        notification = notify.Notification.new.return_value
        notification.show.assert_called()


@given(testkit.environ)
@where(environ__clear=True)
class CreateNotificationBodyTests(unittest.TestCase):
    def test(self, fixtures: Fixtures) -> None:
        build = {"machine": "babette", "build_id": "1554"}
        self.assertEqual(
            "babette has pushed build 1554", handlers.create_notification_body(build)
        )

    def test_custom_message(self, fixtures: Fixtures) -> None:
        environ = fixtures.environ
        build = {"machine": "babette", "build_id": "1554"}

        environ["GBP_WEBHOOK_MESSAGE"] = "test {build_id} test {machine}"
        body = handlers.create_notification_body(build)

        self.assertEqual(body, "test 1554 test babette")


@given(gi=testkit.patch, import_module=testkit.patch)
@where(gi__target="gbp_webhook.handlers.gi")
@where(import_module__target="gbp_webhook.handlers.importlib.import_module")
class InitNotifyTests(unittest.TestCase):
    def test(self, fixtures: Fixtures) -> None:
        gi = fixtures.gi
        import_module = fixtures.import_module

        init_notify.cache_clear()

        notify = init_notify()

        import_module.assert_called_once_with("gi.repository.Notify")
        self.assertEqual(import_module.return_value, notify)

        notify.init.assert_called_once_with("Gentoo Build Publisher")
        notify.set_app_icon.assert_called_once_with(handlers.ICON)

        gi.require_version.assert_called_once_with("Notify", "0.7")
