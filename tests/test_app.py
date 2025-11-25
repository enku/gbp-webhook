"""Tests for the gbp-webhook flask app"""

# pylint: disable=missing-docstring
import concurrent.futures as cf
import unittest

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


@given(eps=testkit.patch)
@where(eps__target="gbp_webhook.app.HANDLERS")
@where(eps__new=[lib.mock_entry_point("postpull"), lib.mock_entry_point("published")])
class HandleEventTests(unittest.TestCase):
    def test_schedules_named_events(self, fixtures: Fixtures) -> None:
        event = {"name": "postpull", "machine": "babette"}
        postpull, published = fixtures.eps

        app.handle_event(event)

        postpull.load.assert_called_once_with()
        handler = postpull.load.return_value
        handler.assert_called_once_with(event)
        published.load.assert_not_called()


@given(executor=testkit.patch)
@where(executor__target="gbp_webhook.app.executor")
class ScheduleHandlerTest(unittest.TestCase):
    def test(self, fixtures: Fixtures) -> None:
        event = {"name": "postpull", "machine": "babette"}
        entry_point = lib.mock_entry_point("postpull")

        app.schedule_handler(entry_point, event)

        handler = entry_point.load.return_value
        fixtures.executor.return_value.submit.assert_called_once_with(handler, event)


class ExecutorTests(unittest.TestCase):
    def test(self) -> None:
        app.executor.cache_clear()

        executor = app.executor()

        self.assertIsInstance(executor, cf.ThreadPoolExecutor)
