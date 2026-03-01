import logging
import multiprocessing
import time
from pathlib import Path

from cyy_naive_lib.concurrency import ProcessPool
from cyy_naive_lib.fs.tempdir import TempDir
from cyy_naive_lib.log import (
    add_file_handler,
    log_debug,
    log_error,
    log_info,
    log_warning,
    remove_file_handler,
    replace_logger,
    set_formatter,
    set_level,
)


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

        assert future.result() == 0, "Child should not spawn extra processes"

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


def test_set_formatter() -> None:
    """Verify custom formatter is applied."""
    with TempDir():
        fmt = logging.Formatter("CUSTOM %(message)s")
        set_formatter(fmt)
        add_file_handler("fmt_test.log")
        log_info("formatted_msg")
        time.sleep(1)
        remove_file_handler("fmt_test.log")

        content = Path("fmt_test.log").read_text(encoding="utf8")
        assert "CUSTOM formatted_msg" in content


def test_replace_logger() -> None:
    """Verify replace_logger routes a named logger through the proxy."""
    with TempDir():
        add_file_handler("replace_test.log")
        set_level(logging.INFO)

        third_party = logging.getLogger("third_party_lib")
        replace_logger("third_party_lib")
        third_party.info("routed_msg")

        time.sleep(1)
        remove_file_handler("replace_test.log")

        content = Path("replace_test.log").read_text(encoding="utf8")
        assert "routed_msg" in content
