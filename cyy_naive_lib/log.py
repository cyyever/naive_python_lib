#!/usr/bin/env python3
import logging
import logging.handlers
import os
import threading
from multiprocessing import Queue

from colorlog import ColoredFormatter


def __set_formatter(_handler, with_color=True, thread_name=None):
    if with_color:
        if os.getenv("eink_screen") == "1":
            with_color = False
    if thread_name is None:
        thread_name = "{thd:%(thread)d}"
    else:
        thread_name = "{" + thread_name + "}"
    __format_str: str = (
        "%(asctime)s %(levelname)s "
        + thread_name
        + " [%(filename)s => %(lineno)d] : %(message)s"
    )
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
        try:
            record = q.get()
            logger.handle(record)
        except EOFError:
            break


__colored_logger: logging.Logger = logging.getLogger("colored_logger")
if not __colored_logger.handlers:
    __colored_logger.setLevel(logging.DEBUG)
    _handler = logging.StreamHandler()
    __set_formatter(_handler, with_color=True)
    __colored_logger.addHandler(_handler)


__stub_colored_logger = logging.getLogger("colored_multiprocess_logger")
if not __stub_colored_logger.handlers:
    __stub_colored_logger.setLevel(logging.INFO)
    queue: Queue = Queue()
    qh = logging.handlers.QueueHandler(queue)
    __stub_colored_logger.addHandler(qh)
    __lp = threading.Thread(
        target=__worker, args=(queue, __colored_logger), daemon=True
    )
    __lp.start()

__thread_name = None


def set_thread_name(thread_name: str):
    global __thread_name
    global __colored_logger
    __thread_name = thread_name
    for _handler in __colored_logger.handlers:
        with_color = True
        if isinstance(_handler, logging.FileHandler):
            with_color = False
        __set_formatter(_handler, with_color=with_color, thread_name=__thread_name)


def set_file_handler(filename: str):
    global __thread_name
    global __colored_logger
    log_dir = os.path.dirname(filename)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    handler = logging.FileHandler(filename)
    __set_formatter(handler, with_color=False, thread_name=__thread_name)
    __colored_logger.addHandler(handler)


def get_logger():
    return __stub_colored_logger
