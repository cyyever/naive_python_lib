import multiprocessing
import threading

from cyy_naive_lib.data_structure.process_pool import ProcessPool
from cyy_naive_lib.data_structure.thread_pool import ThreadPool
from cyy_naive_lib.log import get_logger


def thd_fun():
    get_logger().warning("thread is %s", threading.current_thread())


def process_fun():
    get_logger().warning("process is %s", multiprocessing.current_process())


def test_thread_pool():
    pool = ThreadPool()
    pool.submit(thd_fun)
    pool.shutdown()


def test_process_pool():
    pool: ProcessPool = ProcessPool()
    pool.submit(process_fun)
    pool.shutdown()
