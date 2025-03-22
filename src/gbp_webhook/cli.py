"""gbp-webhook command-line interface"""

import argparse
import os
from typing import TYPE_CHECKING

from . import server, systemd

if TYPE_CHECKING:  # pragma: no cover
    from gbpcli.gbp import GBP
    from gbpcli.types import Console

ACTIONS = {
    "serve": server.serve,
    "install": systemd.install,
    "uninstall": systemd.uninstall,
}
HELP = """The gbp-webhook server

Depending on the action:

  - serve: run the webhook server
  - install install the systemd unit file
  - remove the systemd unit file
"""
DEFAULT_NGINX = os.environ.get("GBP_WEBHOOK_NGINX") or "/usr/sbin/nginx"


def handler(args: argparse.Namespace, _gbp: "GBP", _console: "Console") -> int:
    """Run the gbp-webhook server"""
    ACTIONS[args.action](args)

    return 0


def parse_args(parser: argparse.ArgumentParser) -> None:
    """Set subcommand arguments"""
    parser.add_argument("action", choices=ACTIONS)
    parser.add_argument("-p", "--port", type=int, default=5000)
    parser.add_argument("-a", "--allow", nargs="*", default=[])
    parser.add_argument(
        "--ssl",
        action="store_true",
        default=False,
        help="Listen for SSL (TLS) connections",
    )
    parser.add_argument("--ssl-cert", default=None, help="SSL CA certificate file")
    parser.add_argument("--ssl-key", default=None, help="SSL private key file")
    parser.add_argument(
        "--nginx",
        default=DEFAULT_NGINX,
        help="Path to the nginx executable. default: %(default)s",
    )
