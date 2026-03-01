"""Queue-based multiprocess logging."""

import logging
import sys
from collections.abc import Callable, Iterable, Mapping
from contextlib import redirect_stdout
from typing import Any

from ._env import _LoggerEnv


def get_proxy_logger() -> logging.Logger:
    return _LoggerEnv.initialize_proxy_logger()


def initialize_proxy_logger() -> None:
    _LoggerEnv.initialize_proxy_logger()


class _LoggerPropagator:
    """Picklable wrapper that propagates logger settings to a child process."""

    def __init__(self, fn: Callable, setting: Any) -> None:
        self._fn = fn
        self._setting = setting

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        _LoggerEnv.initialize_proxy_logger(self._setting)
        return self._fn(*args, **kwargs)


def propagate_to_process[T](fn: T) -> T:
    """Wrap a callable so logger settings are auto-propagated in child processes."""
    setting = _LoggerEnv.get_logger_setting()
    if setting is None:
        return fn
    return _LoggerPropagator(fn, setting)  # type: ignore[return-value]


def replace_logger(name: str) -> None:
    _LoggerEnv.replace_logger(name)


def get_replaced_loggers() -> set[str]:
    return _LoggerEnv.get_replaced_loggers()


def replace_default_logger() -> None:
    replace_logger(logging.getLogger().name)


def add_file_handler(filename: str) -> None:
    _LoggerEnv.add_file_handler(filename)


def remove_file_handler(filename: str) -> None:
    _LoggerEnv.remove_file_handler(filename)


def set_level(level: int) -> None:
    _LoggerEnv.set_level(level)


def set_formatter(formatter: logging.Formatter) -> None:
    _LoggerEnv.set_formatter(formatter)


def _make_log_func(level: str):
    method_name = level

    def log_func(
        msg: object,
        *args: object,
        exc_info: bool | tuple | BaseException | None = None,
        stack_info: bool = False,
        extra: Mapping[str, object] | None = None,
    ) -> None:
        getattr(_LoggerEnv.initialize_proxy_logger(), method_name)(
            msg, *args, exc_info=exc_info, stack_info=stack_info, extra=extra, stacklevel=2
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
            logger = get_proxy_logger()
        self.logger = logger

    def write(self, buf: str) -> None:
        self.logger.info("%s", buf)

    def flush(self) -> None:
        for h in self.logger.handlers:
            h.flush()


def redirect_stdout_to_logger(
    logger_names: Iterable[str] | None = None,
) -> redirect_stdout:
    """Redirect stdout through the logging system.

    Optionally replaces named loggers (e.g. third-party library loggers)
    to route their output through the queue-based proxy logger.
    """
    if logger_names is not None:
        for name in logger_names:
            replace_logger(name=name)
    return redirect_stdout(sys.stderr)


__all__ = [
    "StreamToLogger",
    "add_file_handler",
    "get_proxy_logger",
    "get_replaced_loggers",
    "initialize_proxy_logger",
    "propagate_to_process",
    "log_debug",
    "log_error",
    "log_info",
    "log_warning",
    "redirect_stdout_to_logger",
    "remove_file_handler",
    "replace_default_logger",
    "replace_logger",
    "set_formatter",
    "set_level",
]
