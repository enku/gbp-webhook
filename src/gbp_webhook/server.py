"""gbp-webhook gunicorn/nginx server"""

import os
import signal
import subprocess as sp
import sys
import tempfile
from argparse import Namespace
from pathlib import Path
from typing import Any, NoReturn

from . import utils
from .types import NGINX_CONF

APP = "gbp_webhook.app:app"

_CHILDREN: list[sp.Popen] = []


def shutdown(_signalnum: int, _frame: Any) -> NoReturn:
    """Kill children and exit"""
    for child in _CHILDREN:
        child.kill()

    raise SystemExit(0)


@utils.register_signal_handler(signal.SIGTERM, shutdown)
def serve(options: Namespace) -> str:
    """Serve the webhook"""

    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        tmp_path = Path(tmpdir)
        socket = tmp_path / "gunicorn.sock"
        args = [sys.executable, "-m", "gunicorn", "-b", f"unix:{socket}", APP]

        _CHILDREN.append(utils.start_process(args))
        nginx_conf = tmp_path / NGINX_CONF
        nginx_conf.write_text(
            utils.render_template(NGINX_CONF, home=tmpdir, options=options)
        )
        args = [options.nginx, "-e", f"{tmpdir}/error.log", "-c", f"{nginx_conf}"]
        _CHILDREN.append(utils.start_process(args))

        try:
            for child in _CHILDREN:
                child.wait()
        except KeyboardInterrupt:
            shutdown(signal.SIGTERM, None)

    return tmpdir
