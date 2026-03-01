import atexit
import copy
import logging
import logging.handlers
import multiprocessing
import multiprocessing.queues
import os
import sys
import threading
from pathlib import Path
from typing import NotRequired, TypedDict

from colorlog import ColoredFormatter


class LoggerSetting(TypedDict):
    message_queue: multiprocessing.queues.Queue
    replaced_loggers: set[str]
    pid: int
    logger_level: int
    logger_formatter: NotRequired[logging.Formatter]


class _RemoveHandler:
    """Picklable control message to remove a file handler with queue ordering."""

    def __init__(self, filename: str) -> None:
        self.filename = filename


class _LoggerQueueListener(logging.handlers.QueueListener):
    """QueueListener that handles _RemoveHandler control messages."""

    def __init__(
        self, q: multiprocessing.queues.Queue, *handlers: logging.Handler
    ) -> None:
        super().__init__(q, *handlers)
        self._pending_removals: dict[str, threading.Event] = {}
        self._handler_lock = threading.Lock()

    def handle(self, record: logging.LogRecord) -> None:
        if isinstance(record, _RemoveHandler):
            resolved = Path(record.filename)
            with self._handler_lock:
                for h in self.handlers:
                    if (
                        isinstance(h, logging.FileHandler)
                        and Path(h.baseFilename).resolve() == resolved
                    ):
                        self.handlers = tuple(
                            x for x in self.handlers if x is not h
                        )
                        h.flush()
                        h.close()
                        break
            event = self._pending_removals.pop(record.filename, None)
            if event is not None:
                event.set()
            return
        with self._handler_lock:
            super().handle(record)


class _ResilientQueueHandler(logging.handlers.QueueHandler):
    """QueueHandler that falls back to stderr if the queue connection dies."""

    def prepare(self, record: logging.LogRecord) -> logging.LogRecord:
        record = copy.copy(record)
        # Resolve msg % args so args don't need to be picklable.
        # Don't call self.format() here — the listener's handlers will format.
        record.msg = record.getMessage()
        record.args = None
        # Convert traceback to text since traceback objects aren't picklable.
        if record.exc_info and not record.exc_text:
            record.exc_text = logging.Formatter().formatException(record.exc_info)
        record.exc_info = None
        return record

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.enqueue(self.prepare(record))
        except Exception:
            try:
                print(self.format(record), file=sys.stderr)
            except Exception:
                pass


def _create_default_formatter(*, with_color: bool = True) -> logging.Formatter:
    if with_color and os.getenv("EINK_SCREEN") == "1":
        with_color = False
    format_str = (
        "%(asctime)s %(levelname)s {%(processName)s}"
        " [%(filename)s => %(lineno)d] : %(message)s"
    )
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


# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------
_lock = threading.RLock()
_queue: multiprocessing.queues.Queue | None = None
_listener: _LoggerQueueListener | None = None
_proxy_logger: logging.Logger | None = None
_filenames: set[str] = set()
_replaced_loggers: set[str] = set()
_formatter: logging.Formatter | None = None
_level: int = logging.INFO
_is_owner: bool = False


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def initialize_proxy_logger(
    setting: LoggerSetting | None = None,
) -> logging.Logger:
    global _proxy_logger
    # Fast path: skip lock after initialization (_proxy_logger is set once)
    if setting is None and _proxy_logger is not None:
        return _proxy_logger
    with _lock:
        if setting is not None:
            _apply_setting(setting)
        if _proxy_logger is not None:
            return _proxy_logger
        _do_initialize()
        _proxy_logger = logging.getLogger("proxy_logger")
        if _proxy_logger.handlers:
            return _proxy_logger
        assert _queue is not None
        _proxy_logger.addHandler(_ResilientQueueHandler(_queue))
        _proxy_logger.propagate = False
        _proxy_logger.setLevel(_level)
        for name in _replaced_loggers:
            _replace_handlers(name)
        return _proxy_logger


def set_formatter(formatter: logging.Formatter) -> None:
    global _formatter
    with _lock:
        _formatter = formatter
        if _listener is not None:
            with _listener._handler_lock:
                for handler in _listener.handlers:
                    handler.setFormatter(formatter)


def set_level(level: int) -> None:
    global _level
    with _lock:
        _level = level
        if _proxy_logger is not None:
            _proxy_logger.setLevel(level)
        for name in _replaced_loggers:
            logging.getLogger(name=name).setLevel(level)


def replace_logger(name: str) -> None:
    with _lock:
        _replaced_loggers.add(name)
        if _proxy_logger is not None:
            _replace_handlers(name)


def add_file_handler(filename: str) -> None:
    filename = str(Path(filename).resolve())
    with _lock:
        _filenames.add(filename)
        if _listener is None:
            return
        with _listener._handler_lock:
            for h in _listener.handlers:
                if (
                    isinstance(h, logging.FileHandler)
                    and Path(h.baseFilename).resolve() == Path(filename)
                ):
                    return
            file_path = Path(filename)
            if file_path.parent != Path():
                file_path.parent.mkdir(parents=True, exist_ok=True)
            handler = logging.FileHandler(file_path, mode="wt", encoding="utf8")
            if _formatter is not None:
                handler.setFormatter(_formatter)
            else:
                handler.setFormatter(_create_default_formatter(with_color=False))
            _listener.handlers = (*_listener.handlers, handler)


def remove_file_handler(filename: str) -> None:
    filename = str(Path(filename).resolve())
    done: threading.Event | None = None
    with _lock:
        _filenames.discard(filename)
        if _listener is None or _queue is None:
            return
        resolved = Path(filename)
        with _listener._handler_lock:
            for h in _listener.handlers:
                if (
                    isinstance(h, logging.FileHandler)
                    and Path(h.baseFilename).resolve() == resolved
                ):
                    done = threading.Event()
                    _listener._pending_removals[filename] = done
                    _queue.put(_RemoveHandler(filename))
                    break
    if done is not None:
        done.wait(timeout=10)


def get_logger_setting() -> LoggerSetting | None:
    with _lock:
        if _queue is None:
            return None
        setting = LoggerSetting(
            message_queue=_queue,
            replaced_loggers=_replaced_loggers.copy(),
            pid=os.getpid(),
            logger_level=_level,
        )
        if _formatter is not None:
            setting["logger_formatter"] = _formatter
        return setting


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _replace_handlers(name: str) -> None:
    """Replace a named logger's handlers with the proxy logger's handlers.

    Must be called while _lock is held and _proxy_logger is set.
    """
    assert _proxy_logger is not None
    replaced = logging.getLogger(name=name)
    for h in replaced.handlers[:]:
        replaced.removeHandler(h)
    for h in _proxy_logger.handlers:
        replaced.addHandler(h)
    replaced.setLevel(_level)


def _apply_setting(setting: LoggerSetting) -> None:
    """Apply logger settings from a parent process.

    Must be called while _lock is held.
    """
    global _queue, _formatter, _level
    if os.getpid() == setting["pid"]:
        return
    if _queue is None:
        _queue = setting["message_queue"]
    if "logger_formatter" in setting:
        _formatter = setting["logger_formatter"]
    if "logger_level" in setting:
        _level = setting["logger_level"]
    _replaced_loggers.update(setting["replaced_loggers"])


def _do_initialize() -> None:
    """Set up queue, listener, and stream handler.

    Must be called while _lock is held.
    """
    global _queue, _is_owner, _listener
    if _proxy_logger is not None:
        return
    if _queue is None:
        _queue = multiprocessing.get_context("spawn").Queue()
        _is_owner = True

    if not _is_owner:
        return

    stream_handler = logging.StreamHandler()
    if _formatter is not None:
        stream_handler.setFormatter(_formatter)
    else:
        stream_handler.setFormatter(_create_default_formatter(with_color=True))

    _listener = _LoggerQueueListener(_queue, stream_handler)
    _listener.start()

    # Create file handlers for any filenames added before initialization
    for filename in _filenames:
        add_file_handler(filename)

    @atexit.register
    def _shutdown() -> None:
        if _listener is not None:
            _listener.stop()
            for h in _listener.handlers:
                try:
                    h.flush()
                    h.close()
                except (ValueError, OSError):
                    pass
