"""Webhook event handlers"""

import os
from typing import Any

import gi

gi.require_version("Notify", "0.7")

# pylint: disable=wrong-import-position
from gi.repository import Notify

from .types import Event

ICON = os.environ.get("GBP_WEBHOOK_ICON") or "package-x-generic"

Notify.init("Gentoo Build Publisher")
Notify.set_app_icon(ICON)  # type: ignore


def build_pulled(event: Event) -> None:
    """build_pulled event handler"""
    title = event["machine"]
    body = create_notification_body(event["data"]["build"])
    notification = Notify.Notification.new(title, body, ICON)
    notification.show()


def create_notification_body(build: dict[str, Any]) -> str:
    """Return the notification body"""
    machine: str = build["machine"]
    build_id: str = build["build_id"]

    return f"{machine} has pushed build {build_id}"
