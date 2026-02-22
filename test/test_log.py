import contextlib
import logging
import multiprocessing
import os
import threading
import time
from collections.abc import Generator
from pathlib import Path

from cyy_naive_lib.concurrency import ProcessPool
from cyy_naive_lib.fs.tempdir import TempDir
from cyy_naive_lib.log import (
    add_file_handler,
    get_logger_setting,
    get_replaced_loggers,
    log_debug,
    log_error,
    log_info,
    log_warning,
    remove_file_handler,
    replace_logger,
    set_level,
)


@contextlib.contextmanager
def _saved_env(key: str) -> Generator[None]:
    """Save and restore an environment variable."""
    old = os.environ.pop(key, None)
    try:
        yield
    finally:
        if old is not None:
            os.environ[key] = old
        else:
            os.environ.pop(key, None)


def _child_worker() -> int:
    """Logs numbered messages in a child process, returns active subprocess count.

    A correctly behaving child should not start its own worker subprocess —
    it should reuse the parent's queue and worker.
    """
    for i in range(10):
        log_info("child_msg_%d", i)
    time.sleep(0.5)
    return len(multiprocessing.active_children())


def test_file_handler_and_multiprocess() -> None:
    """Verify logging output from both parent and child processes.

    Checks:
    - File handler captures messages (not just no-crash)
    - Log level filtering works (debug filtered at INFO level)
    - Child process messages reach the parent's file handler
    - Child does not start a competing worker subprocess
    """
    with TempDir():
        add_file_handler("test.log")

        # Exercise log levels from parent
        set_level(logging.INFO)
        log_debug("filtered_debug")
        log_info("parent_info")
        log_warning("parent_warning")
        log_error("parent_error")

        # Log from child process
        pool = ProcessPool()
        future = pool.submit(_child_worker)
        pool.wait_results()
        pool.shutdown()

        # Child must not start its own worker
        child_subprocess_count = future.result()
        assert child_subprocess_count == 0, (
            f"Child started {child_subprocess_count} subprocess(es); "
            "expected 0 (child should not start its own worker)"
        )

        # Wait for worker to flush, then verify file content
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


def test_get_logger_setting_copies_filenames() -> None:
    """Verify get_logger_setting returns a snapshot, not a mutable reference."""
    log_info("init")
    with TempDir():
        add_file_handler("file1.log")
        setting = get_logger_setting()
        assert setting is not None
        filenames_before = setting["filenames"].copy()

        add_file_handler("file2.log")

        assert setting["filenames"] == filenames_before, (
            "get_logger_setting returned a mutable reference to internal filenames"
        )

        remove_file_handler("file1.log")
        remove_file_handler("file2.log")


def test_replaced_loggers() -> None:
    """Verify replace_logger accumulates and get_replaced_loggers is non-destructive."""
    with _saved_env("CYY_REPLACED_LOGGER"):
        replace_logger("first")
        replace_logger("second")
        replace_logger("third")

        # Multiple reads must return the same result
        result1 = get_replaced_loggers()
        result2 = get_replaced_loggers()
        assert result1 == result2 == {"first", "second", "third"}


def test_logger_setting_thread_safety() -> None:
    """Verify concurrent access to logger settings doesn't crash."""
    log_info("init")

    errors: list[Exception] = []

    def reader() -> None:
        try:
            for _ in range(200):
                setting = get_logger_setting()
                assert setting is not None
        except Exception as e:
            errors.append(e)

    def writer() -> None:
        try:
            for _ in range(200):
                set_level(logging.DEBUG)
                set_level(logging.INFO)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=reader) for _ in range(4)]
    threads += [threading.Thread(target=writer) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Thread safety errors: {errors}"
