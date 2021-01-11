import logging
from log import get_logger, set_file_handler
from fs.tempdir import TempDir
from util import readlines


def test_log():
    with TempDir():
        set_file_handler("./log")
        get_logger().debug("debug msg")
        get_logger().setLevel(logging.INFO)
        get_logger().debug("no debug msg")
        get_logger().info("info msg")
        get_logger().error("error msg")
        get_logger().info("file content %s", readlines("./log"))
