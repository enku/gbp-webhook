"""Tests for gbp-webhook handlers"""

# pylint: disable=missing-docstring

import unittest
from unittest import mock

from gbp_webhook import handlers

patch = mock.patch


@patch.object(handlers, "Notify")
class BuildPulledTests(unittest.TestCase):
    def test(self, notify: mock.Mock) -> None:
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
