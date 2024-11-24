import multiprocessing
import threading

from cyy_naive_lib.concurrency import ProcessPool, ThreadPool
from cyy_naive_lib.log import log_warning


def thd_fun():
    log_warning("thread is %s", threading.current_thread())


def process_fun():
    log_warning("process is %s", multiprocessing.current_process())


def test_thread_pool():
    pool = ThreadPool()
    pool.submit(thd_fun)
    pool.shutdown()


def test_process_pool() -> None:
    pool: ProcessPool = ProcessPool()
    pool.submit(process_fun)
    pool.shutdown()
