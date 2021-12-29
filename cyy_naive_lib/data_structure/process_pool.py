import concurrent.futures

from .executor_pool import ExecutorPool


class ProcessPool(ExecutorPool):
    def __init__(self, max_workers=None):
        super().__init__(
            concurrent.futures.ProcessPoolExecutor(max_workers=max_workers)
        )
