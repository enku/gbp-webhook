"""gbp-webhook type definitions"""

from typing import Any, TypeAlias

NGINX_CONF = "nginx.conf"
WEBHOOK_CONF = "gbp-webhook.conf"
Event: TypeAlias = dict[str, Any]
