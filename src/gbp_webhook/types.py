"""gbp-webhook type definitions"""

from typing import Any

type Event = dict[str, Any]

NGINX_CONF = "nginx.conf"
WEBHOOK_CONF = "gbp-webhook.conf"
