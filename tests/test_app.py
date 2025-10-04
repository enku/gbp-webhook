"""Tests for the gbp-webhook flask app"""

# pylint: disable=missing-docstring
import concurrent.futures as cf
import unittest
from unittest import mock

import gbp_testkit.fixtures as testkit
from unittest_fixtures import Fixtures, given, where

from gbp_webhook import app, handlers

from . import lib


@given(lib.client, executor=testkit.patch, pre_shared_key=testkit.patch)
@where(pre_shared_key__target="gbp_webhook.app.PRE_SHARED_KEY")
@where(pre_shared_key__new="key")
@where(executor__target="gbp_webhook.app.executor")
class WebhookTests(unittest.TestCase):
    def test(self, fixtures: Fixtures) -> None:
        client = fixtures.client
        headers = {"X-Pre-Shared-Key": fixtures.pre_shared_key}
        build = {"machine": "babette", "build_id": "1554"}
        event = {"name": "postpull", "machine": "babette", "data": {"build": build}}

        response = client.post("/webhook", json=event, headers=headers)

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            {"message": "Notification handled!", "status": "success"}, response.json
        )
        fixtures.executor.return_value.submit.assert_called_once_with(
            handlers.postpull, event
        )

    def test_invalid_key(self, fixtures: Fixtures) -> None:
        client = fixtures.client
        headers = {"X-Pre-Shared-Key": fixtures.pre_shared_key + "xxx"}
        build = {"machine": "babette", "build_id": "1554"}
        event = {"name": "postpull", "machine": "babette", "data": {"build": build}}

        response = client.post("/webhook", json=event, headers=headers)

        self.assertEqual(403, response.status_code)
        self.assertEqual(
            {"message": "Invalid pre-shared key!", "status": "error"}, response.json
        )
        fixtures.executor.assert_not_called()


@given(executor=testkit.patch)
@where(executor__target="gbp_webhook.app.executor")
class HandleEventTests(unittest.TestCase):
    def test_schedules_named_events(self, fixtures: Fixtures) -> None:
        executor = fixtures.executor.return_value
        executor.submit.side_effect = lambda handler, event: handler(event)
        entry_points = [mock_entry_point("postpull") for _ in range(3)]
        entry_points.append(published := mock_entry_point("build_published"))
        event = {"name": "postpull", "machine": "babette"}

        with mock.patch.object(app, "HANDLERS", new=entry_points):
            app.handle_event(event)

        for entry_point in entry_points[:3]:
            entry_point.load.assert_called_once_with()
            handler = entry_point.load.return_value
            handler.assert_called_once_with(event)
        published.load.assert_not_called()


@given(executor=testkit.patch)
@where(executor__target="gbp_webhook.app.executor")
class ScheduleHandlerTest(unittest.TestCase):
    def test(self, fixtures: Fixtures) -> None:
        event = {"name": "postpull", "machine": "babette"}
        entry_point = mock_entry_point("postpull")

        app.schedule_handler(entry_point, event)

        handler = entry_point.load.return_value
        fixtures.executor.return_value.submit.assert_called_once_with(handler, event)


class ExecutorTests(unittest.TestCase):
    def test(self) -> None:
        app.executor.cache_clear()

        executor = app.executor()

        self.assertIsInstance(executor, cf.ThreadPoolExecutor)


def mock_entry_point(event: str) -> mock.Mock:
    entry_point = mock.Mock()
    entry_point.name = event

    return entry_point
