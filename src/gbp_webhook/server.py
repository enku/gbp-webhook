"""gbp-webhook gunicorn/nginx server"""

import os
import signal
import sys
import tempfile
from argparse import Namespace
from pathlib import Path
from typing import Any, NoReturn

from . import utils
from .types import NGINX_CONF

APP = "gbp_webhook.app:app"


def shutdown(_signalnum: int, _frame: Any) -> NoReturn:
    """exit"""
    raise SystemExit(0)


@utils.register_signal_handler(signal.SIGINT, shutdown)
@utils.register_signal_handler(signal.SIGTERM, shutdown)
def serve(options: Namespace) -> str:
    """Serve the webhook"""

    with tempfile.TemporaryDirectory() as tmpdir, utils.ChildProcess() as children:
        os.chdir(tmpdir)
        tmp_path = Path(tmpdir)
        socket = tmp_path / "gunicorn.sock"
        args = [sys.executable, "-m", "gunicorn", "-b", f"unix:{socket}", APP]

        children.add(args)
        nginx_conf = tmp_path / NGINX_CONF
        nginx_conf.write_text(
            utils.render_template(NGINX_CONF, home=tmpdir, options=options)
        )
        args = [options.nginx, "-e", f"{tmpdir}/error.log", "-c", f"{nginx_conf}"]
        children.add(args)

    return tmpdir
