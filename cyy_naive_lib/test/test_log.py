import logging
from log import get_logger, set_logger_level


def test_log():
    get_logger().debug("debug msg")
    set_logger_level(logging.INFO)
    get_logger().debug("no debug msg")
    get_logger().info("info msg")
