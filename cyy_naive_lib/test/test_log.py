import logging
from log import default_logger


def test_log():
    default_logger.debug("debug msg")
    default_logger.setLevel(logging.INFO)
    default_logger.debug("no debug msg")
    default_logger.info("info msg")
    default_logger.error("info msg")
