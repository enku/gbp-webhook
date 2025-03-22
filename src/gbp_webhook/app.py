"""gbp-webhook flask app"""

import importlib.metadata
import os
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

    if headers.get(PSK_HEADER) != PRE_SHARED_KEY:
        return jsonify({"status": "error", "message": "Invalid pre-shared key!"}), 403

    event = cast(Event, request.json)
    event_name = event["name"]

    for entry_point in HANDLERS:
        if entry_point.name == event_name:
            handler: Callable[[Event], Any] = entry_point.load()
            handler(event)

    return jsonify({"status": "success", "message": "Notification handled!"}), 200
