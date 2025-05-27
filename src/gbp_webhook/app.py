"""gbp-webhook flask app"""

import concurrent.futures as cf
import importlib.metadata
import os
from functools import cache
from typing import Any, Callable, cast

from flask import Flask, Response, jsonify, request

from .types import Event

EP_GROUP = "gbp_webhook.handlers"
HANDLERS = importlib.metadata.entry_points(group=EP_GROUP)
PRE_SHARED_KEY = os.environ.get("GBP_WEBHOOK_PRE_SHARED_KEY", "")
PSK_HEADER = os.environ.get("GBP_WEBHOOK_PSK_HEADER") or "X-Pre-Shared-Key"

app = Flask("webhook")


@app.route("/webhook", methods=["POST"])
def webhook() -> tuple[Response, int]:
    """Webhook responder"""
    headers = request.headers
    event = cast(Event, request.json)

    if headers.get(PSK_HEADER) != PRE_SHARED_KEY:
        return jsonify({"status": "error", "message": "Invalid pre-shared key!"}), 403

    for entry_point in HANDLERS:
        schedule_handler(entry_point, event)

    return jsonify({"status": "success", "message": "Notification handled!"}), 200


def schedule_handler(entry_point: importlib.metadata.EntryPoint, event: Event) -> bool:
    """Schedule the EntryPoint on the event if the entrypoint is named for the event

    Return True.
    If the entry_point is not registered for the event return False.
    """
    if entry_point.name != event["name"]:
        return False

    handler: Callable[[Event], Any] = entry_point.load()
    executor().submit(handler, event)
    return True


@cache
def executor() -> cf.ThreadPoolExecutor:
    """Create and return a ThreadPoolExecutor"""
    return cf.ThreadPoolExecutor()
