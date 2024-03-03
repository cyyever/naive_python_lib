import concurrent.futures
import threading

from .executor_pool import ExecutorPool


class ThreadPool(ExecutorPool):
    def __init__(self) -> None:
        super().__init__(concurrent.futures.ThreadPoolExecutor())
        self.__stop_event = threading.Event()

    def repeated_exec(self, *args, **kwargs) -> None:
        super()._repeated_exec(stop_event=self.__stop_event, *args, **kwargs)
