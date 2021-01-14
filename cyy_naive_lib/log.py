#!/usr/bin/env python3
import atexit
import logging
import logging.handlers
import os
import sys
import threading
from multiprocessing import Queue

from colorlog import ColoredFormatter

__colored_logger: logging.Logger = logging.getLogger("colored_logger")


def __set_formatter(_handler, with_color=True):
    __format_str: str = "%(asctime)s %(levelname)s {thd:%(thread)d} [%(filename)s => %(lineno)d] : %(message)s"
    if with_color:
        formatter = ColoredFormatter(
            "%(log_color)s" + __format_str,
            log_colors={
                "DEBUG": "green",
                "INFO": "white",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
            style="%",
        )
    else:
        formatter = logging.Formatter(
            __format_str,
            style="%",
        )

    _handler.setFormatter(formatter)


def __logger_thread(q):
    while True:
        record = q.get()
        if record is None:
            break
        __colored_logger.handle(record)
        for handler in __colored_logger.handlers:
            handler.flush()


__initialized = False

for _handler in __colored_logger.handlers:
    if isinstance(_handler, logging.StreamHandler):
        if _handler.stream == sys.stderr:
            __initialized = True

__q: Queue = Queue()
if not __initialized:
    __colored_logger.setLevel(logging.DEBUG)
    _handler = logging.StreamHandler()
    with_color = True
    if os.getenv("eink_screen") == "1":
        with_color = False
    __set_formatter(_handler, with_color=with_color)
    __colored_logger.addHandler(_handler)
    __lp = threading.Thread(target=__logger_thread, args=(__q,), daemon=True)
    __lp.start()

    def __exit_handler():
        global __q
        global __lp
        __q.put(None)

    atexit.register(__exit_handler)
    __initialized = True


def set_file_handler(filename: str):
    global __colored_logger
    log_dir = os.path.dirname(filename)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    _handler = logging.FileHandler(filename)
    __set_formatter(_handler, with_color=False)
    __colored_logger.addHandler(_handler)


def get_logger():
    logger = logging.getLogger("colored_multiprocess_logger")
    if not logger.handlers:
        qh = logging.handlers.QueueHandler(__q)
        logger.addHandler(qh)
        logger.setLevel(logging.DEBUG)
    return logger
