import multiprocessing
import threading

from cyy_naive_lib.data_structure.process_pool import ProcessPool
from cyy_naive_lib.data_structure.thread_pool import ThreadPool


def thd_fun():
    print("thread is", threading.current_thread())


def process_fun():
    print("process is", multiprocessing.current_process())


def test_thread_pool():
    pool = ThreadPool()
    pool.submit(thd_fun)
    pool.stop()


def test_process_pool():
    pool: ProcessPool = ProcessPool()
    pool.submit(process_fun)
    pool.stop()
