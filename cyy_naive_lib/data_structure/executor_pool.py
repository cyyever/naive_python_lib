import concurrent.futures
import traceback
from typing import Callable

from log import get_logger


class ExecutorPool:
    def __init__(self, executor, stop_event):
        self.executor = executor
        self.stop_event = stop_event
        self.futures = []

    def stop(self):
        self.stop_event.set()
        concurrent.futures.wait(self.futures)
        self.stop_event.clear()

    def repeated_exec(self, sleep_time: float, fn: Callable, *args, **kwargs):
        def process():
            while True:
                try:
                    fn(*args, **kwargs)
                except Exception as e:
                    get_logger().error("catch exception:%s", e)
                    get_logger().error("traceback:%s", traceback.format_exc())
                if self.stop_event.wait(sleep_time):
                    break

        self.futures.append(self.executor.submit(process))

    def exec(self, fn: Callable, *args, **kwargs):
        def process():
            try:
                fn(*args, **kwargs)
            except Exception as e:
                get_logger().error("catch exception:%s", e)
                get_logger().error("traceback:%s", traceback.format_exc())

        self.futures.append(self.executor.submit(process))
