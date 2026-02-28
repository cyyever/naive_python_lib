import atexit
import contextlib
import logging
import logging.handlers
import multiprocessing
import multiprocessing.managers
import os
import sys
import threading
from multiprocessing.queues import Queue
from pathlib import Path
from typing import ClassVar

from ._types import LoggerSetting, set_logger_level
from ._worker import worker


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


class _LoggerEnv:
    _lock = threading.RLock()
    _manager: multiprocessing.managers.SyncManager | None = None
    _queue: Queue | None = None
    _worker_process: multiprocessing.process.BaseProcess | None = None
    _proxy_logger: logging.Logger | None = None
    _filenames: ClassVar[set[str]] = set()
    _replaced_loggers: ClassVar[set[str]] = set()
    _formatter: logging.Formatter | None = None
    _level: int = logging.DEBUG
    _is_owner: bool = False

    @classmethod
    def _put(cls, msg: dict) -> None:
        """Send a control message to the worker. Only the queue owner may call this."""
        if cls._queue is not None and cls._is_owner:
            cls._queue.put(msg)

    @classmethod
    def initialize_proxy_logger(cls) -> logging.Logger:
        with cls._lock:
            if cls._proxy_logger is not None:
                return cls._proxy_logger
            cls._initialize()
            cls._proxy_logger = logging.getLogger("proxy_logger")
            if cls._proxy_logger.handlers:
                return cls._proxy_logger
            assert cls._queue is not None
            cls._proxy_logger.addHandler(_ResilientQueueHandler(cls._queue))
            cls._proxy_logger.propagate = False
            if cls._is_owner:
                cls._send_all_settings()
            set_logger_level(cls._proxy_logger, cls._level)
            for name in cls._replaced_loggers:
                replaced = logging.getLogger(name=name)
                for h in replaced.handlers[:]:
                    replaced.removeHandler(h)
                for h in cls._proxy_logger.handlers:
                    replaced.addHandler(h)
            return cls._proxy_logger

    @classmethod
    def _send_all_settings(cls) -> None:
        if cls._queue is None:
            return
        cls._queue.put({"logger_level": cls._level})
        if cls._formatter is not None:
            cls._queue.put({"logger_formatter": cls._formatter})
        for f in cls._filenames:
            cls._queue.put({"filename": f})

    @classmethod
    def set_formatter(cls, formatter: logging.Formatter) -> None:
        with cls._lock:
            cls._formatter = formatter
            cls._put({"logger_formatter": formatter})

    @classmethod
    def set_level(cls, level: int) -> None:
        with cls._lock:
            cls._level = level
            cls._put({"logger_level": level})

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
            cls._put({"filename": filename})

    @classmethod
    def remove_file_handler(cls, filename: str) -> None:
        filename = str(Path(filename).resolve())
        with cls._lock:
            cls._filenames.discard(filename)
            assert cls._queue is not None and cls._manager is not None
            done = cls._manager.Event()
            cls._queue.put({"removed_filename": filename, "done_event": done})
        done.wait(timeout=10)

    @classmethod
    def get_logger_setting(cls) -> LoggerSetting | None:
        with cls._lock:
            if cls._queue is None:
                return None
            setting = LoggerSetting(
                message_queue=cls._queue,
                filenames=cls._filenames.copy(),
                replaced_loggers=cls._replaced_loggers.copy(),
                pid=os.getpid(),
                logger_level=cls._level,
            )
            if cls._formatter is not None:
                setting["logger_formatter"] = cls._formatter
            return setting

    @classmethod
    def apply_logger_setting(cls, setting: LoggerSetting | None = None) -> None:
        """Apply logger settings from a parent process (spawn or fork)."""
        with cls._lock:
            if not setting or os.getpid() == setting["pid"]:
                return
            if cls._queue is None:
                cls._queue = setting["message_queue"]
            if "logger_formatter" in setting:
                cls._formatter = setting["logger_formatter"]
            if "logger_level" in setting:
                cls._level = setting["logger_level"]
            cls._filenames.update(setting["filenames"])
            cls._replaced_loggers.update(setting["replaced_loggers"])

    @classmethod
    def _initialize(cls) -> None:
        with cls._lock:
            if cls._proxy_logger is not None:
                return
            if cls._queue is None:
                prev_dir = Path.cwd()
                try:
                    os.chdir(Path.home())
                except OSError:
                    prev_dir = None
                try:
                    cls._manager = multiprocessing.get_context("spawn").Manager()
                    cls._queue = cls._manager.Queue()  # type: ignore[assignment]
                    cls._is_owner = True
                finally:
                    if prev_dir is not None:
                        with contextlib.suppress(OSError):
                            os.chdir(prev_dir)

            if not cls._is_owner:
                return

            cls._worker_process = multiprocessing.get_context("spawn").Process(
                target=worker,
                args=(cls._queue, os.getpid()),
                daemon=False,
            )
            cls._worker_process.start()

            @atexit.register
            def shutdown() -> None:
                try:
                    if cls._queue is not None:
                        cls._queue.put({"cyy_logger_exit": os.getpid()})
                    if cls._worker_process is not None:
                        cls._worker_process.join(timeout=10)
                        if cls._worker_process.is_alive():
                            cls._worker_process.terminate()
                except Exception:
                    pass
                try:
                    if cls._manager is not None:
                        cls._manager.shutdown()
                except Exception:
                    pass
