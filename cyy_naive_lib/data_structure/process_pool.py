import concurrent.futures
import multiprocessing

from .executor_pool import ExecutorPool


class ProcessPool(ExecutorPool):
    def __init__(self):
        super().__init__(
            concurrent.futures.ProcessPoolExecutor(), multiprocessing.Event()
        )
