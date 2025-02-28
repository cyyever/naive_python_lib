import concurrent.futures

from .executor import ExecutorWrapper


class ThreadPool(ExecutorWrapper):
    def __init__(self) -> None:
        super().__init__(executor=concurrent.futures.ThreadPoolExecutor())
