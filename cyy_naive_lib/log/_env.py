import atexit
import logging
import logging.handlers
import multiprocessing
import multiprocessing.queues
import os
import sys
import threading
from pathlib import Path
from typing import ClassVar

from colorlog import ColoredFormatter

from ._types import LoggerSetting, set_logger_level


class _RemoveHandler:
    """Control message to remove a file handler with queue ordering guarantee."""

    def __init__(self, handler: logging.FileHandler, event: threading.Event) -> None:
        self.handler = handler
        self.event = event


class _LoggerQueueListener(logging.handlers.QueueListener):
    """QueueListener that handles _RemoveHandler control messages."""

    def handle(self, record: logging.LogRecord) -> None:
        if isinstance(record, _RemoveHandler):
            self.handlers = tuple(h for h in self.handlers if h is not record.handler)
            record.handler.flush()
            record.handler.close()
            record.event.set()
            return
        super().handle(record)


class _ResilientQueueHandler(logging.handlers.QueueHandler):
    """QueueHandler that falls back to stderr if the queue connection dies."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            super().emit(record)
        except (BrokenPipeError, ConnectionRefusedError, EOFError, OSError):
            try:
                print(self.format(record), file=sys.stderr)
            except Exception:
                pass


def _create_default_formatter(*, with_color: bool = True) -> logging.Formatter:
    if with_color and os.getenv("EINK_SCREEN") == "1":
        with_color = False
    format_str = "%(asctime)s %(levelname)s {%(processName)s} [%(filename)s => %(lineno)d] : %(message)s"
    if with_color:
        return ColoredFormatter(
            "%(log_color)s" + format_str,
            log_colors={
                "DEBUG": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
            style="%",
        )
    return logging.Formatter(format_str, style="%")


class _LoggerEnv:
    _lock = threading.RLock()
    _queue: multiprocessing.queues.Queue | None = None
    _listener: _LoggerQueueListener | None = None
    _proxy_logger: logging.Logger | None = None
    _filenames: ClassVar[set[str]] = set()
    _replaced_loggers: ClassVar[set[str]] = set()
    _formatter: logging.Formatter | None = None
    _level: int = logging.INFO
    _is_owner: bool = False

    @classmethod
    def initialize_proxy_logger(
        cls, setting: LoggerSetting | None = None
    ) -> logging.Logger:
        with cls._lock:
            if setting is not None:
                cls._apply_logger_setting(setting)
            if cls._proxy_logger is not None:
                return cls._proxy_logger
            cls._initialize()
            cls._proxy_logger = logging.getLogger("proxy_logger")
            if cls._proxy_logger.handlers:
                return cls._proxy_logger
            assert cls._queue is not None
            cls._proxy_logger.addHandler(_ResilientQueueHandler(cls._queue))
            cls._proxy_logger.propagate = False
            set_logger_level(cls._proxy_logger, cls._level)
            for name in cls._replaced_loggers:
                replaced = logging.getLogger(name=name)
                for h in replaced.handlers[:]:
                    replaced.removeHandler(h)
                for h in cls._proxy_logger.handlers:
                    replaced.addHandler(h)
            return cls._proxy_logger

    @classmethod
    def set_formatter(cls, formatter: logging.Formatter) -> None:
        with cls._lock:
            cls._formatter = formatter
            if cls._listener is not None:
                for handler in cls._listener.handlers:
                    handler.setFormatter(formatter)

    @classmethod
    def set_level(cls, level: int) -> None:
        with cls._lock:
            cls._level = level
            if cls._proxy_logger is not None:
                set_logger_level(cls._proxy_logger, level)

    @classmethod
    def replace_logger(cls, name: str) -> None:
        with cls._lock:
            cls._replaced_loggers.add(name)

    @classmethod
    def get_replaced_loggers(cls) -> set[str]:
        with cls._lock:
            return cls._replaced_loggers.copy()

    @classmethod
    def add_file_handler(cls, filename: str) -> None:
        filename = str(Path(filename).resolve())
        with cls._lock:
            cls._filenames.add(filename)
            if cls._listener is None:
                return
            for h in cls._listener.handlers:
                if isinstance(h, logging.FileHandler) and Path(
                    h.baseFilename
                ).resolve() == Path(filename):
                    return
            file_path = Path(filename)
            if file_path.parent != Path():
                file_path.parent.mkdir(parents=True, exist_ok=True)
            handler = logging.FileHandler(file_path, mode="wt", encoding="utf8")
            if cls._formatter is not None:
                handler.setFormatter(cls._formatter)
            else:
                handler.setFormatter(_create_default_formatter(with_color=False))
            cls._listener.handlers = (*cls._listener.handlers, handler)

    @classmethod
    def remove_file_handler(cls, filename: str) -> None:
        filename = str(Path(filename).resolve())
        done: threading.Event | None = None
        with cls._lock:
            cls._filenames.discard(filename)
            if cls._listener is None or cls._queue is None:
                return
            resolved = Path(filename)
            for h in cls._listener.handlers:
                if (
                    isinstance(h, logging.FileHandler)
                    and Path(h.baseFilename).resolve() == resolved
                ):
                    done = threading.Event()
                    cls._queue.put(_RemoveHandler(h, done))
                    break
        if done is not None:
            done.wait(timeout=10)

    @classmethod
    def get_logger_setting(cls) -> LoggerSetting | None:
        with cls._lock:
            if cls._queue is None:
                return None
            setting = LoggerSetting(
                message_queue=cls._queue,
                replaced_loggers=cls._replaced_loggers.copy(),
                pid=os.getpid(),
                logger_level=cls._level,
            )
            if cls._formatter is not None:
                setting["logger_formatter"] = cls._formatter
            return setting

    @classmethod
    def _apply_logger_setting(cls, setting: LoggerSetting) -> None:
        """Apply logger settings from a parent process (spawn or fork).

        Must be called while cls._lock is held.
        """
        if os.getpid() == setting["pid"]:
            return
        if cls._queue is None:
            cls._queue = setting["message_queue"]
        if "logger_formatter" in setting:
            cls._formatter = setting["logger_formatter"]
        if "logger_level" in setting:
            cls._level = setting["logger_level"]
        cls._replaced_loggers.update(setting["replaced_loggers"])

    @classmethod
    def _initialize(cls) -> None:
        with cls._lock:
            if cls._proxy_logger is not None:
                return
            if cls._queue is None:
                cls._queue = multiprocessing.get_context("spawn").Queue()
                cls._is_owner = True

            if not cls._is_owner:
                return

            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(_create_default_formatter(with_color=True))

            cls._listener = _LoggerQueueListener(cls._queue, stream_handler)
            cls._listener.start()

            @atexit.register
            def shutdown() -> None:
                if cls._listener is not None:
                    cls._listener.stop()
