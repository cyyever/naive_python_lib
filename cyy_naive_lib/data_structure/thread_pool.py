import concurrent.futures
import threading

from .executor_pool import ExecutorPool


class ThreadPool(ExecutorPool):
    def __init__(self):
        super().__init__(concurrent.futures.ThreadPoolExecutor(), threading.Event())
