import concurrent.futures
import threading
import traceback
from typing import Callable
from log import get_logger


class ThreadPool:
    def __init__(self):
        self.executor = concurrent.futures.ThreadPoolExecutor()
        self.stop_event = threading.Event()
        self.futures = []

    def stop(self):
        self.stop_event.set()
        concurrent.futures.wait(self.futures)
        self.stop_event.clear()

    def repeated_exec(
            self,
            loop_interval: float,
            fn: Callable,
            *args,
            **kwargs):
        def process():
            while True:
                try:
                    fn(*args, **kwargs)
                except Exception as e:
                    get_logger().error("catch exception:%s", e)
                    get_logger().error("traceback:%s", traceback.format_exc())
                if self.stop_event.wait(loop_interval):
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
