import logging
import logging.handlers
import os
import threading
from multiprocessing import Queue
from typing import Any

from colorlog import ColoredFormatter


def __set_default_formatter(handler: logging.Handler, with_color: bool = True) -> None:
    if with_color and os.getenv("eink_screen") == "1":
        with_color = False
    format_str: str = "%(asctime)s %(levelname)s {%(processName)s} [%(filename)s => %(lineno)d] : %(message)s"
    if with_color:
        formatter: logging.Formatter = ColoredFormatter(
            "%(log_color)s" + format_str,
            log_colors={
                "DEBUG": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
            style="%",
        )
    else:
        formatter = logging.Formatter(
            format_str,
            style="%",
        )

    handler.setFormatter(formatter)


def __worker(
    queue: Queue, logger: logging.Logger, logger_lock: threading.RLock
) -> None:
    while True:
        try:
            record = queue.get()
            if record is None:
                return
            with logger_lock:
                logger.handle(record)
        except ValueError:
            return
        except EOFError:
            return


__logger_lock = threading.RLock()
__colored_logger: logging.Logger = logging.getLogger("colored_logger")
if not __colored_logger.handlers:
    __colored_logger.setLevel(logging.DEBUG)
    __handler = logging.StreamHandler()
    __set_default_formatter(__handler, with_color=True)
    __colored_logger.addHandler(__handler)
    __colored_logger.propagate = False


__stub_colored_logger = logging.getLogger("colored_multiprocess_logger")
if not __stub_colored_logger.handlers:
    __stub_colored_logger.setLevel(logging.INFO)
    q: Queue = Queue()
    __stub_colored_logger.addHandler(logging.handlers.QueueHandler(q))
    __stub_colored_logger.propagate = False
    __background_thd = threading.Thread(
        target=__worker, args=(q, __colored_logger, __logger_lock)
    )
    __background_thd.start()
    threading._register_atexit(__background_thd.join, None)
    threading._register_atexit(q.put, None)


def add_file_handler(filename: str) -> logging.Handler:
    filename = os.path.normpath(os.path.abspath(filename))
    with __logger_lock:
        for handler in __colored_logger.handlers:
            if (
                isinstance(handler, logging.FileHandler)
                and handler.baseFilename == filename
            ):
                return handler
        log_dir = os.path.dirname(filename)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        handler = logging.FileHandler(filename)
        __set_default_formatter(handler, with_color=False)
        __colored_logger.addHandler(handler)
        return handler


def set_level(level: Any) -> None:
    with __logger_lock:
        __stub_colored_logger.setLevel(level)


# def set_formatter(formatter) -> None:
#     with __logger_lock:
#         for handler in __colored_logger.handlers:
#             handler.setFormatter(formatter)


def get_logger_setting() -> dict:
    setting: dict = {}
    with __logger_lock:
        setting["level"] = __stub_colored_logger.level
        setting["handlers"] = []
        for handler in __colored_logger.handlers:
            handler_dict: dict = {"formatter": handler.formatter}
            if isinstance(handler, logging.FileHandler):
                handler_dict["type"] = "file"
                handler_dict["filename"] = handler.baseFilename
            elif isinstance(handler, logging.StreamHandler):
                handler_dict["type"] = "stream"
            else:
                raise NotImplementedError()
            setting["handlers"].append(handler_dict)
    return setting


def apply_logger_setting(setting: dict) -> None:
    with __logger_lock:
        set_level(setting["level"])
        for handler_info in setting["handlers"]:
            if handler_info["type"] == "stream":
                handler = __colored_logger.handlers[0]
                assert isinstance(handler, logging.StreamHandler)
            elif handler_info["type"] == "file":
                handler = add_file_handler(handler_info["filename"])
            else:
                raise NotImplementedError()
            handler.setFormatter(handler_info["formatter"])


def get_logger():
    return __stub_colored_logger
