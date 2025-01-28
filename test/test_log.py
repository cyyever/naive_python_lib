import logging
import multiprocessing

from cyy_naive_lib.concurrency import ProcessPool
from cyy_naive_lib.fs.tempdir import TempDir
from cyy_naive_lib.log import (
    add_file_handler,
    remove_file_handler,
    log_debug,
    log_error,
    log_info,
    log_warning,
    set_level,
)


def __test_log() -> None:
    log_debug("debug msg")
    set_level(logging.INFO)
    log_debug("no debug msg")
    log_info("info msg")
    log_warning("warning msg")
    log_error("error msg")


def test_log() -> None:
    with TempDir():
        multiprocessing.current_process().name = "my process"
        add_file_handler("log")
        remove_file_handler("log")
        # with open("log", encoding="utf8") as f:
        #     file_content = f.readlines()
        #     log_info("file content %s", file_content)
        #     assert file_content


def test_multiprocess_log() -> None:
    pool = ProcessPool()
    pool.submit(__test_log)
    pool.shutdown()
