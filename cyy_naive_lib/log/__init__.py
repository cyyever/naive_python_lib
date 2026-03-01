"""Queue-based multiprocess logging."""

import logging
import sys
from collections.abc import Callable, Mapping
from contextlib import redirect_stdout
from typing import Any

from . import _env


class _LoggerPropagator:
    """Picklable wrapper that propagates logger settings to a child process."""

    def __init__(self, fn: Callable, setting: Any) -> None:
        self._fn = fn
        self._setting = setting

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        _env.initialize_proxy_logger(self._setting)
        return self._fn(*args, **kwargs)


def propagate_to_process[T](fn: T) -> T:
    """Wrap a callable so logger settings are auto-propagated in child processes."""
    setting = _env.get_logger_setting()
    if setting is None:
        return fn
    return _LoggerPropagator(fn, setting)  # type: ignore[return-value]


def replace_logger(*names: str) -> None:
    """Replace named loggers' handlers with the proxy logger's handlers.

    If no names given, replaces the root logger.
    """
    if not names:
        names = (logging.getLogger().name,)
    for name in names:
        _env.replace_logger(name)


def add_file_handler(filename: str) -> None:
    _env.add_file_handler(filename)


def remove_file_handler(filename: str) -> None:
    _env.remove_file_handler(filename)


def set_level(level: int) -> None:
    _env.set_level(level)


def set_formatter(formatter: logging.Formatter) -> None:
    _env.set_formatter(formatter)


def _make_log_func(level: str) -> Callable:
    method_name = level

    def log_func(
        msg: object,
        *args: object,
        exc_info: bool | tuple | BaseException | None = None,
        stack_info: bool = False,
        extra: Mapping[str, object] | None = None,
    ) -> None:
        getattr(_env.initialize_proxy_logger(), method_name)(
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            extra=extra,
            stacklevel=2,
        )

    log_func.__name__ = log_func.__qualname__ = f"log_{level}"
    return log_func


log_debug = _make_log_func("debug")
log_info = _make_log_func("info")
log_warning = _make_log_func("warning")
log_error = _make_log_func("error")


class StreamToLogger:
    """Fake file-like stream object that redirects writes to a logger.

    Useful for capturing third-party library output that writes to stdout/stderr.
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        if logger is None:
            logger = _env.initialize_proxy_logger()
        self.logger = logger

    def write(self, buf: str) -> None:
        buf = buf.rstrip()
        if buf:
            self.logger.info("%s", buf)

    def flush(self) -> None:
        pass


def redirect_stdout_to_logger(*logger_names: str) -> redirect_stdout:
    """Redirect stdout to stderr and optionally replace named loggers."""
    if logger_names:
        replace_logger(*logger_names)
    return redirect_stdout(sys.stderr)


__all__ = [
    "StreamToLogger",
    "add_file_handler",
    "log_debug",
    "log_error",
    "log_info",
    "log_warning",
    "propagate_to_process",
    "redirect_stdout_to_logger",
    "remove_file_handler",
    "replace_logger",
    "set_formatter",
    "set_level",
]
