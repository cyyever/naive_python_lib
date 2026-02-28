import logging
from multiprocessing import Queue
from typing import NotRequired, TypedDict


class LoggerSetting(TypedDict):
    message_queue: Queue
    filenames: set[str]
    replaced_loggers: set[str]
    pid: int
    logger_level: int
    logger_formatter: NotRequired[logging.Formatter]


def set_logger_level(logger: logging.Logger, level: int) -> None:
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)
