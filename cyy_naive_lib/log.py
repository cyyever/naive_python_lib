#!/usr/bin/env python3
import os
import sys
import logging
from colorlog import ColoredFormatter


default_logger: logging.RootLogger = logging.root


def __set_formatter(handler, with_color=True):
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

    handler.setFormatter(formatter)


__initialized = False

for handler in default_logger.handlers:
    if isinstance(handler, logging.StreamHandler):
        if handler.stream == sys.stderr:
            __initialized = True

if not __initialized:
    handler = logging.StreamHandler()
    __set_formatter(handler)
    default_logger.addHandler(handler)
    default_logger.setLevel(logging.DEBUG)
    __initialized = True


def set_file_handler(filename: str):
    global default_logger
    log_dir = os.path.dirname(filename)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    handler = logging.FileHandler(filename)
    __set_formatter(handler, with_color=False)
    default_logger.addHandler(handler)


def get_logger():
    global default_logger
    return default_logger
