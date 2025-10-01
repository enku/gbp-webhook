"""gbp-webhook utility functions"""

import os
import signal
import subprocess as sp
import sys
from types import FrameType
from typing import Any, Callable, Iterable, NoReturn, Self, Sequence

from gbpcli import get_user_config
from jinja2 import Environment, PackageLoader, select_autoescape
from yarl import URL

type SignalHandler = Callable[[int, FrameType | None], Any]
_env = Environment(loader=PackageLoader("gbp_webhook"), autoescape=select_autoescape())


def render_template(name: str, **context) -> str:
    """Render the given app template with the given context"""
    template = _env.get_template(name)

    return template.render(**context)


def get_command_path(argv: Sequence[str] | None = None) -> str:
    """Return the path of the current command"""
    if argv is None:
        argv = sys.argv

    if (arg0 := argv[0]).startswith("/"):
        return arg0

    if path := getattr(sys.modules["__main__"], "__file__", None):
        return os.path.abspath(path)

    raise RuntimeError("Cannot locate exe path")


class ChildProcess:
    """Context manager to start child processes and await them when exited"""

    # Signals we catch while awaiting children
    signals = (signal.SIGINT, signal.SIGTERM)

    def __init__(self) -> None:
        self._children: list[sp.Popen] = []
        self.orig_handlers: list[SignalHandler | int | None] = []

    def add(self, *args: str) -> sp.Popen:
        """Start and add a child process with the given args"""
        # pylint: disable=consider-using-with
        self._children.append(sp.Popen(args))
        return self._children[-1]

    def shutdown(self, *_args: Any) -> NoReturn:
        """Kill children and exit"""
        for child in self._children:
            child.kill()

        raise SystemExit(0)

    def __enter__(self) -> Self:
        for signalnum in self.signals:
            self.orig_handlers.append(signal.getsignal(signalnum))
            signal.signal(signalnum, self.shutdown)

        return self

    def __exit__(self, *args: Any) -> None:
        for child in self._children:
            child.wait()

        for signalnum, orig in zip(self.signals, self.orig_handlers):
            signal.signal(signalnum, orig)


def remove_from_lst(lst: Iterable[str], items: Iterable[str]) -> list[str]:
    """Return a list containing lst with the (first occurrence of) items removed"""
    lst = list(lst)

    for item in items:
        try:
            lst.remove(item)
        except ValueError:
            pass

    return lst


def build_url(machine: str, build_id: str) -> str:
    """Return the url for the build with the given machine and build_id"""
    config = get_user_config(os.environ.get("GBPCLI_CONFIG"))
    base_url = config.url

    assert isinstance(base_url, str)

    url = URL(base_url).joinpath("machines", machine, "builds", f"{build_id}/")

    return str(url)
