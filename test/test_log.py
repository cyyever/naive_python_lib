import logging
import multiprocessing
import time
from pathlib import Path

import pytest

from cyy_naive_lib.concurrency import ProcessPool
from cyy_naive_lib.fs.tempdir import TempDir
from cyy_naive_lib.log import (
    add_file_handler,
    log_debug,
    log_error,
    log_info,
    log_warning,
    remove_file_handler,
    set_level,
)

_has_fork = "fork" in multiprocessing.get_all_start_methods()


def _child_worker() -> int:
    for i in range(10):
        log_info("child_msg_%d", i)
    time.sleep(0.5)
    return len(multiprocessing.active_children())


def test_file_handler_and_multiprocess() -> None:
    """Verify file handler, log level filtering, and child process logging."""
    with TempDir():
        add_file_handler("test.log")
        set_level(logging.INFO)
        log_debug("filtered_debug")
        log_info("parent_info")
        log_warning("parent_warning")
        log_error("parent_error")

        pool = ProcessPool()
        future = pool.submit(_child_worker)
        pool.wait_results()
        pool.shutdown()

        assert future.result() == 0, "Child should not start its own worker"

        time.sleep(2)
        remove_file_handler("test.log")
        time.sleep(0.5)

        content = Path("test.log").read_text(encoding="utf8")
        assert "filtered_debug" not in content
        assert "parent_info" in content
        assert "parent_warning" in content
        assert "parent_error" in content
        for i in range(10):
            assert f"child_msg_{i}" in content, f"Missing child_msg_{i}"


@pytest.mark.skipif(not _has_fork, reason="fork not available on this platform")
def test_fork_process_pool_logging() -> None:
    """Verify logging works correctly with a fork-based process pool."""
    log_info("init")
    with TempDir():
        add_file_handler("fork_test.log")
        set_level(logging.INFO)

        fork_ctx = multiprocessing.get_context("fork")
        pool = ProcessPool(mp_context=fork_ctx)
        future = pool.submit(_child_worker)
        pool.wait_results()
        pool.shutdown()

        assert future.result() == 0, "Child should not start its own worker"

        time.sleep(2)
        remove_file_handler("fork_test.log")
        time.sleep(0.5)

        content = Path("fork_test.log").read_text(encoding="utf8")
        for i in range(10):
            assert f"child_msg_{i}" in content, f"Missing child_msg_{i}"
