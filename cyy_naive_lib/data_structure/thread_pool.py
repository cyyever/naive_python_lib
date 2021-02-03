import concurrent.futures
import threading
import traceback
from typing import Callable

from log import get_logger

from .executor_pool import ExecutorPool


class ThreadPool(ExecutorPool):
    def __init__(self, stop_event=threading.Event()):
        super().__init__(concurrent.futures.ThreadPoolExecutor())
        self.stop_event = stop_event

    def stop(self):
        self.stop_event.set()
        super().stop()
        self.stop_event.clear()

    def repeated_exec(self, sleep_time: float, fn: Callable, *args, **kwargs):
        def worker():
            while True:
                try:
                    fn(*args, **kwargs)
                except Exception as e:
                    get_logger().error("catch exception:%s", e)
                    get_logger().error("traceback:%s", traceback.format_exc())
                if self.stop_event.wait(sleep_time):
                    break

        self.futures.append(self.executor.submit(worker))
