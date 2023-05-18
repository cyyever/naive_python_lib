import logging
import threading

from cyy_naive_lib.fs.tempdir import TempDir
from cyy_naive_lib.log import get_logger


def test_log():
    with TempDir():
        threading.current_thread().name = "my thd"
        get_logger().debug("debug msg")
        get_logger().setLevel(logging.INFO)
        get_logger().debug("no debug msg")
        get_logger().info("info msg")
        get_logger().error("error msg")
        # add_file_handler("log")
        # with open("log", "rt", encoding="utf8") as f:
        #     file_content = f.readlines()
        #     get_logger().info("file content %s", file_content)
        #     assert file_content
