"""Webhook event handlers"""

import importlib
import os
from functools import cache
from types import ModuleType
from typing import Any

import gi

from .types import Event

ICON = os.environ.get("GBP_WEBHOOK_ICON") or "package-x-generic"
APP_ICON = os.environ.get("GBP_WEBHOOK_APP_ICON", ICON)


def build_pulled(event: Event) -> None:
    """build_pulled event handler"""
    notify = init_notify()
    title = event["machine"]
    body = create_notification_body(event["data"]["build"])
    notification = notify.Notification.new(title, body, ICON)
    notification.show()


def create_notification_body(build: dict[str, Any]) -> str:
    """Return the notification body"""
    machine: str = build["machine"]
    build_id: str = build["build_id"]

    return f"{machine} has pushed build {build_id}"


@cache
def init_notify() -> ModuleType:
    """Initialize the gi Notify namespace"""
    gi.require_version("Notify", "0.7")
    notify = importlib.import_module("gi.repository.Notify")
    notify.init("Gentoo Build Publisher")
    notify.set_app_icon(APP_ICON)  # type: ignore

    return notify
