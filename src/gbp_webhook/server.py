"""gbp-webhook gunicorn/nginx server"""

import os
import sys
import tempfile
from argparse import Namespace
from pathlib import Path

from .types import NGINX_CONF
from .utils import ChildProcess, render_template

APP = "gbp_webhook.app:app"


def serve(options: Namespace) -> str:
    """Serve the webhook"""

    with tempfile.TemporaryDirectory() as tmpdir, ChildProcess() as procs:
        os.chdir(tmpdir)
        tmp_path = Path(tmpdir)
        socket = tmp_path / "gunicorn.sock"

        procs.add(sys.executable, "-m", "gunicorn", "-b", f"unix:{socket}", APP)
        nginx_conf = tmp_path / NGINX_CONF
        nginx_conf.write_text(render_template(NGINX_CONF, home=tmpdir, options=options))
        procs.add(options.nginx, "-e", f"{tmpdir}/error.log", "-c", f"{nginx_conf}")

    return tmpdir
