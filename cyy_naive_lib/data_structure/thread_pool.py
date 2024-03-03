import concurrent.futures
import threading

from .executor_pool import ExecutorPool


class ThreadPool(ExecutorPool):
    def __init__(self) -> None:
        super().__init__(concurrent.futures.ThreadPoolExecutor())
        self.__stop_event = threading.Event()

    def _repeated_exec(self, *args, **kwargs) -> None:
        super()._repeated_exec(self.__stop_event, *args, **kwargs)
