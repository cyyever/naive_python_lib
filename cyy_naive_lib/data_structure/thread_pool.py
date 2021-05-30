import concurrent.futures
import threading
from typing import Callable

from .executor_pool import ExecutorPool


class ThreadPool(ExecutorPool):
    def __init__(self, stop_event=threading.Event()):
        super().__init__(concurrent.futures.ThreadPoolExecutor())
        self.__stop_event = stop_event

    def stop(self):
        self.__stop_event.set()
        super().stop()
        self.__stop_event.clear()

    def repeated_exec(self, sleep_time: float, fn: Callable, *args, **kwargs):
        super()._repeated_exec(self.__stop_event, sleep_time, fn, *args, **kwargs)
