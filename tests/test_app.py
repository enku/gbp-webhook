"""Tests for the gbp-webhook flask app"""

# pylint: disable=missing-docstring
import concurrent.futures as cf
import unittest
from unittest import mock

from unittest_fixtures import Fixtures, given

from gbp_webhook import app, handlers

from . import lib


@given(lib.pre_shared_key)
@given(lib.executor)
class WebhookTests(unittest.TestCase):
    def test(self, fixtures: Fixtures) -> None:
        client = app.app.test_client()
        headers = {"X-Pre-Shared-Key": fixtures.pre_shared_key}
        build = {"machine": "babette", "build_id": "1554"}
        event = {"name": "build_pulled", "machine": "babette", "data": {"build": build}}

        response = client.post("/webhook", json=event, headers=headers)

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            {"message": "Notification handled!", "status": "success"}, response.json
        )
        fixtures.executor.return_value.submit.assert_called_once_with(
            handlers.build_pulled, event
        )

    def test_invalid_key(self, fixtures: Fixtures) -> None:
        client = app.app.test_client()
        headers = {"X-Pre-Shared-Key": fixtures.pre_shared_key + "xxx"}
        build = {"machine": "babette", "build_id": "1554"}
        event = {"name": "build_pulled", "machine": "babette", "data": {"build": build}}

        response = client.post("/webhook", json=event, headers=headers)

        self.assertEqual(403, response.status_code)
        self.assertEqual(
            {"message": "Invalid pre-shared key!", "status": "error"}, response.json
        )
        fixtures.executor.assert_not_called()


@given(lib.executor)
class ScheduleHandlerTest(unittest.TestCase):
    def test_true(self, fixtures: Fixtures) -> None:
        event = {"name": "build_pulled", "machine": "babette"}
        entry_point = mock.Mock()
        entry_point.name = "build_pulled"

        self.assertIs(True, app.schedule_handler(entry_point, event))

        handler = entry_point.load.return_value
        fixtures.executor.return_value.submit.assert_called_once_with(handler, event)

    def test_false(self, fixtures: Fixtures) -> None:
        event = {"name": "build_pulled", "machine": "babette"}
        entry_point = mock.Mock()
        entry_point.name = "bogus"

        self.assertIs(False, app.schedule_handler(entry_point, event))
        fixtures.executor.return_value.submit.assert_not_called()


class ExecutorTests(unittest.TestCase):
    def test(self) -> None:
        app.executor.cache_clear()

        executor = app.executor()

        self.assertIsInstance(executor, cf.ThreadPoolExecutor)
