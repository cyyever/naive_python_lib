import logging
import multiprocessing

from cyy_naive_lib.fs.tempdir import TempDir
from cyy_naive_lib.log import get_logger, log_debug, log_error, log_info


def test_log():
    with TempDir():
        multiprocessing.current_process().name = "my process"
        log_debug("debug msg")
        get_logger().setLevel(logging.INFO)
        log_debug("no debug msg")
        log_info("info msg")
        get_logger().warning("warning msg")
        log_error("error msg")
        # add_file_handler("log")
        # with open("log", "rt", encoding="utf8") as f:
        #     file_content = f.readlines()
        #     get_logger().info("file content %s", file_content)
        #     assert file_content
