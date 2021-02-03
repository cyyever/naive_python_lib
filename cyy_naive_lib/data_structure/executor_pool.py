import concurrent.futures
import traceback
from typing import Callable

from log import get_logger


class ExecutorPool:
    def __init__(self, executor):
        self.executor = executor
        self.futures = []

    def stop(self):
        concurrent.futures.wait(self.futures)
        for f in self.futures:
            get_logger().info("future result is %s", f.result())

    @staticmethod
    def process_once(fn, *args, **kwargs):
        try:
            fn(*args, **kwargs)
        except Exception as e:
            get_logger().error("catch exception:%s", e)
            get_logger().error("traceback:%s", traceback.format_exc())

    def exec(self, fn: Callable, *args, **kwargs):
        self.futures.append(
            self.executor.submit(ExecutorPool.process_once, fn, *args, **kwargs)
        )
