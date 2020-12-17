import logging
from log import default_logger, set_file_handler
from fs.tempdir import TempDir


def test_log():
    with TempDir():
        set_file_handler("./log")
        default_logger.debug("debug msg")
        default_logger.setLevel(logging.INFO)
        default_logger.debug("no debug msg")
        default_logger.info("info msg")
        default_logger.error("error msg")
        default_logger.info("file content %s", open("./log", "rt").readlines())
