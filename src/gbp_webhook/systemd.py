"""Utils for installing systemd unit files"""

import argparse
import os
import sys
from pathlib import Path
from typing import Iterable

from . import utils
from .types import WEBHOOK_CONF

UNIT = "gbp-webhook.service"


def install(_args: argparse.Namespace) -> None:
    """Install the systemd unit for the user

    No config file (gbp-webhook.conf) exists one will be installed as well.
    """
    unit_dir = get_unit_dir()
    unit_dir.mkdir(parents=True, exist_ok=True)
    unit_path = unit_dir / "gbp-webhook.service"
    config_path = get_config_path()
    config_path.parent.mkdir(exist_ok=True)

    if not config_path.exists():
        args_str = args_from_argv(sys.argv)
        config = utils.render_template(WEBHOOK_CONF, args=repr(args_str))
        config_path.write_text(config, encoding="utf8")

    exe = utils.get_command_path()
    unit = utils.render_template(UNIT, gbp_path=exe, config_path=config_path)
    unit_path.write_text(unit, encoding="utf8")


def uninstall(_args: argparse.Namespace) -> None:
    """Uninstall the unit file, if it exists"""
    unit_dir = get_unit_dir()
    unit_path = unit_dir / "gbp-webhook.service"

    unit_path.unlink(missing_ok=True)


def get_unit_dir() -> Path:
    """Return the directory Path where user units are to be stored"""
    env = os.environ
    xdg_data_home = env.get("XDG_DATA_HOME", None)
    data_home = Path(xdg_data_home) if xdg_data_home else Path.home()

    return data_home.joinpath(".local/share/systemd/user")


def get_config_path() -> Path:
    """Return the path of the config file"""
    return Path.home().joinpath(".config", WEBHOOK_CONF)


def args_from_argv(argv: Iterable[str]) -> str:
    """Convert argv list to a string, removing "gbp webhook install"."""
    argv = list(argv)[1:]

    argv.remove("webhook")
    argv.remove("install")

    return " ".join(argv)
