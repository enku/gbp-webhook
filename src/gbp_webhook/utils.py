"""gbp-webhook utility functions"""

import os
import signal
import subprocess as sp
import sys
from types import FrameType
from typing import Any, Callable, Iterable, NoReturn, ParamSpec, Self, TypeVar

from jinja2 import Environment, PackageLoader, select_autoescape

P = ParamSpec("P")
Tr = TypeVar("Tr")

_env = Environment(loader=PackageLoader("gbp_webhook"), autoescape=select_autoescape())


def render_template(name: str, **context) -> str:
    """Render the given app template with the given context"""
    template = _env.get_template(name)

    return template.render(**context)


def get_command_path() -> str:
    """Return the path of the current command"""
    arg0 = sys.argv[0]

    if arg0.startswith("/"):
        return arg0

    main = sys.modules["__main__"]
    if path := getattr(main, "__file__", None):
        return os.path.abspath(path)

    raise RuntimeError("Cannot locate exe path")


class ChildProcess:
    """Context manager to start child processes and await them when exited"""

    # Signals we catch while awaiting children
    signals = (signal.SIGINT, signal.SIGTERM)

    def __init__(self) -> None:
        self._children: list[sp.Popen] = []
        self.orig_handlers: list[
            Callable[[int, FrameType | None], Any] | int | None
        ] = []

    def add(self, args: Iterable[str]) -> sp.Popen:
        """Start and add a child process with the given args"""
        # pylint: disable=consider-using-with
        self._children.append(sp.Popen(tuple(args)))
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
