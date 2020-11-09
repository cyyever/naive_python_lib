#!/usr/bin/env python3
import os
import logging
from colorlog import ColoredFormatter


default_logger = logging.root


def __set_formatter(handler):
    handler.setFormatter(
        ColoredFormatter(
            "%(log_color)s%(asctime)s %(levelname)s {thd:%(thread)d} [%(filename)s => %(lineno)d] : %(message)s",
            log_colors={
                "DEBUG": "green",
                "INFO": "white",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
            style="%",
        ))


handler = logging.StreamHandler()

__set_formatter(handler)
default_logger.addHandler(handler)
default_logger.setLevel(logging.DEBUG)


def set_file_handle(filename):
    global default_logger
    log_dir = os.path.dirname(filename)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    handler = logging.FileHandler(filename)
    __set_formatter(handler)
    default_logger.addHandler(handler)


def get_logger():
    global default_logger
    return default_logger
