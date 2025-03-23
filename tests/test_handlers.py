"""Tests for gbp-webhook handlers"""

# pylint: disable=missing-docstring

import unittest
from unittest import mock

from gbp_webhook import handlers

patch = mock.patch
init_notify = handlers.init_notify


def setUpModule():  # pylint: disable=invalid-name
    p = patch.object(handlers, "init_notify")
    unittest.addModuleCleanup(p.stop)
    p.start()


class BuildPulledTests(unittest.TestCase):
    def test(self) -> None:
        notify = handlers.init_notify()
        build = {"machine": "babette", "build_id": "1554"}
        event = {"name": "build_pulled", "machine": "babette", "data": {"build": build}}

        handlers.build_pulled(event)

        notify.Notification.new.assert_called_once_with(
            "babette", "babette has pushed build 1554", handlers.ICON
        )
        notification = notify.Notification.new.return_value
        notification.show.assert_called()


class CreateNotificationBodyTests(unittest.TestCase):
    def test(self) -> None:
        build = {"machine": "babette", "build_id": "1554"}
        self.assertEqual(
            "babette has pushed build 1554", handlers.create_notification_body(build)
        )


@patch.object(handlers.importlib, "import_module")
@patch.object(handlers, "gi")
class InitNotifyTests(unittest.TestCase):
    def test(self, gi: mock.Mock, import_module: mock.Mock) -> None:
        init_notify.cache_clear()

        notify = init_notify()

        import_module.assert_called_once_with("gi.repository.Notify")
        self.assertEqual(import_module.return_value, notify)

        notify.init.assert_called_once_with("Gentoo Build Publisher")
        notify.set_app_icon.assert_called_once_with(handlers.ICON)

        gi.require_version.assert_called_once_with("Notify", "0.7")
