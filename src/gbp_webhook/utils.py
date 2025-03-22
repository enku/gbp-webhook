"""gbp-webhook utility functions"""

import os
import signal
import subprocess as sp
import sys
from functools import wraps
from types import FrameType
from typing import Any, Callable, ParamSpec, TypeVar

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


def start_process(args: list[str]) -> sp.Popen:
    """Start and return a process with the given args"""
    return sp.Popen(args)
