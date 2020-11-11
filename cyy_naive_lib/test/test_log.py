import tempfile
import os
import logging
from log import default_logger, set_file_handler


def test_log():
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdirname:
        os.chdir(tmpdirname)
        set_file_handler("./log")
        default_logger.debug("debug msg")
        default_logger.setLevel(logging.INFO)
        default_logger.debug("no debug msg")
        default_logger.info("info msg")
        default_logger.error("error msg")
        default_logger.info("file content %s", open("./log", "rt").readlines())
        os.chdir(cwd)
