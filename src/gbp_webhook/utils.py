"""gbp-webhook utility functions"""

import os
import signal
import subprocess as sp
import sys
from functools import wraps
from types import FrameType
from typing import Any, Callable, ParamSpec, Self, Sequence, TypeVar

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


def register_signal_handler(
    signalnum: int, handler: Callable[[int, FrameType | None], Any]
):
    """Decorator factory for registering a given signal with a handler"""

    def wrapper(fn: Callable[P, Tr]):
        @wraps(fn)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> Tr:
            original_handler = signal.getsignal(signalnum)
            signal.signal(signalnum, handler)
            try:
                return fn(*args, **kwargs)
            finally:
                signal.signal(signalnum, original_handler)

        return wrapped

    return wrapper


class ChildProcess:
    """Context manager to start child processes and await them when exited"""

    def __init__(self) -> None:
        self._children: list[sp.Popen] = []

    def add(self, args: Sequence[str]) -> sp.Popen:
        """Start and add a child process with the given args"""
        # pylint: disable=consider-using-with
        self._children.append(sp.Popen(args))
        return self._children[-1]

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: Any) -> None:
        for child in self._children:
            child.wait()
