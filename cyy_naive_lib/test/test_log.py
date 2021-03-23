import logging

from fs.tempdir import TempDir
from log import get_logger, set_file_handler


def test_log():
    with TempDir():
        get_logger().debug("debug msg")
        get_logger().setLevel(logging.INFO)
        get_logger().debug("no debug msg")
        get_logger().info("info msg")
        get_logger().error("error msg")
        # set_file_handler("./log")
        # with open("./log", "rt") as f:
        #     get_logger().info("file content %s", f.readlines())
