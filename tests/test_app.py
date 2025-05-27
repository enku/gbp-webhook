"""Tests for the gbp-webhook flask app"""

# pylint: disable=missing-docstring
import concurrent.futures as cf
import unittest
from unittest import mock

from gbp_webhook import app, handlers

patch = mock.patch


@patch.object(app, "PRE_SHARED_KEY", "our-little-secret")
@patch.object(app, "executor")
class WebhookTests(unittest.TestCase):
    def test(self, executor: mock.Mock) -> None:
        client = app.app.test_client()
        headers = {"X-Pre-Shared-Key": "our-little-secret"}
        build = {"machine": "babette", "build_id": "1554"}
        event = {"name": "build_pulled", "machine": "babette", "data": {"build": build}}

        response = client.post("/webhook", json=event, headers=headers)

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            {"message": "Notification handled!", "status": "success"}, response.json
        )
        executor.return_value.submit.assert_called_once_with(
            handlers.build_pulled, event
        )

    def test_invalid_key(self, build_pulled: mock.Mock) -> None:
        client = app.app.test_client()
        headers = {"X-Pre-Shared-Key": "the-wrong-key"}
        build = {"machine": "babette", "build_id": "1554"}
        event = {"name": "build_pulled", "machine": "babette", "data": {"build": build}}

        response = client.post("/webhook", json=event, headers=headers)

        self.assertEqual(403, response.status_code)
        self.assertEqual(
            {"message": "Invalid pre-shared key!", "status": "error"}, response.json
        )
        build_pulled.assert_not_called()


@mock.patch.object(app, "executor")
class ScheduleHandlerTest(unittest.TestCase):
    def test_true(self, executor: mock.Mock) -> None:
        event = {"name": "build_pulled", "machine": "babette"}
        entry_point = mock.Mock()
        entry_point.name = "build_pulled"

        self.assertIs(True, app.schedule_handler(entry_point, event))

        handler = entry_point.load.return_value
        executor.return_value.submit.assert_called_once_with(handler, event)

    def test_false(self, executor: mock.Mock) -> None:
        event = {"name": "build_pulled", "machine": "babette"}
        entry_point = mock.Mock()
        entry_point.name = "bogus"

        self.assertIs(False, app.schedule_handler(entry_point, event))
        executor.return_value.submit.assert_not_called()


class ExecutorTests(unittest.TestCase):
    def test(self) -> None:
        app.executor.cache_clear()

        executor = app.executor()

        self.assertIsInstance(executor, cf.ThreadPoolExecutor)
