#!/usr/bin/env python3
import atexit
import logging
import logging.handlers
import os
import threading
from multiprocessing import Queue

from colorlog import ColoredFormatter


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


def __worker(q, logger):
    while True:
        record = q.get()
        if record is None:
            break
        logger.handle(record)


__q: Queue = Queue()
__colored_logger: logging.Logger = logging.getLogger("colored_logger")
if not __colored_logger.handlers:
    __colored_logger.setLevel(logging.DEBUG)
    _handler = logging.StreamHandler()
    with_color = True
    if os.getenv("eink_screen") == "1":
        with_color = False
    __set_formatter(_handler, with_color=with_color)
    __colored_logger.addHandler(_handler)
    __lp = threading.Thread(target=__worker, args=(__q, __colored_logger), daemon=True)
    __lp.start()

    def __exit_handler():
        global __q
        global __lp
        __q.put(None)

    atexit.register(__exit_handler)

__stub_colored_logger = logging.getLogger("colored_multiprocess_logger")
if not __stub_colored_logger.handlers:
    qh = logging.handlers.QueueHandler(__q)
    __stub_colored_logger.addHandler(qh)


def set_file_handler(filename: str):
    global __colored_logger
    log_dir = os.path.dirname(filename)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    handler = logging.FileHandler(filename)
    __set_formatter(handler, with_color=False)
    __colored_logger.addHandler(handler)


def get_logger():
    global __stub_colored_logger
    __stub_colored_logger.setLevel(logging.DEBUG)
    return __stub_colored_logger
