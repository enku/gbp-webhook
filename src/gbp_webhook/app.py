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

    if headers.get(PSK_HEADER) == PRE_SHARED_KEY:
        handle_event(cast(Event, request.json))
        return response("success", "Notification handled!"), 200

    return response("error", "Invalid pre-shared key!"), 403


def handle_event(event: Event) -> None:
    """Schedule the given event to the event handlers"""
    for entry_point in [ep for ep in HANDLERS if ep.name == event["name"]]:
        schedule_handler(entry_point, event)


def schedule_handler(entry_point: importlib.metadata.EntryPoint, event: Event) -> None:
    """Schedule the EntryPoint on the event if the entrypoint is named for the event"""
    handler: Callable[[Event], Any] = entry_point.load()
    executor().submit(handler, event)


def response(status: str, message: str) -> Response:
    """Return a JSON response given the status and message"""
    return jsonify({"status": status, "message": message})


@cache
def executor() -> cf.ThreadPoolExecutor:
    """Create and return a ThreadPoolExecutor"""
    return cf.ThreadPoolExecutor()
