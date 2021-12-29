import concurrent.futures

from .executor_pool import ExecutorPool


class ProcessPool(ExecutorPool):
    def __init__(self, mp_context=None, max_workers=None):
        super().__init__(
            concurrent.futures.ProcessPoolExecutor(
                mp_context=mp_context, max_workers=max_workers
            )
        )
