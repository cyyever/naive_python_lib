import concurrent.futures

from .executor_pool import ExecutorPool


class ThreadPool(ExecutorPool):
    def __init__(self) -> None:
        super().__init__(concurrent.futures.ThreadPoolExecutor())
