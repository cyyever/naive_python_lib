import multiprocessing
import threading
import time

from cyy_naive_lib.data_structure.process_pool import ProcessPool
from cyy_naive_lib.data_structure.thread_pool import ThreadPool


def thd_fun():
    print("thread is", threading.current_thread())


def process_fun():
    print("process is", multiprocessing.current_process())


def test_thread_pool():
    pool = ThreadPool()
    pool.exec(thd_fun)
    pool.repeated_exec(1, thd_fun)
    time.sleep(2)
    pool.stop()


def test_process_pool():
    pool: ProcessPool = ProcessPool()
    pool.exec(process_fun)
    pool.stop()
