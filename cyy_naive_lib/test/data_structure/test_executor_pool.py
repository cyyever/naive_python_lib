import multiprocessing
import threading

from data_structure.process_pool import ProcessPool
from data_structure.thread_pool import ThreadPool


def test_thread_pool():
    pool = ThreadPool()
    pool.exec(lambda: print("thread is", threading.current_thread()))
    pool.stop()


def test_process_pool():
    pool = ProcessPool()
    pool.exec(lambda: print("process is", multiprocessing.current_process()))
    pool.stop()
