import logging
import threading

from log import get_logger, set_file_handler

from fs.tempdir import TempDir


def test_log():
    with TempDir():
        threading.current_thread().name = "my thd"
        get_logger().debug("debug msg")
        get_logger().setLevel(logging.INFO)
        get_logger().debug("no debug msg")
        get_logger().info("info msg")
        get_logger().error("error msg")
        # set_file_handler("log")
        # with open("log", "rt") as f:
        #     file_content = f.readlines()
        #     get_logger().info("file content %s", file_content)
        #     assert file_content
