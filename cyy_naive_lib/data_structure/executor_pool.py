import concurrent.futures
import traceback
from typing import Callable, List

from log import get_logger


class ExecutorPool:
    def __init__(self, executor):
        self.executor = executor
        self.futures: List[concurrent.futures.Future] = []

    def stop(self):
        concurrent.futures.wait(self.futures)
        for f in self.futures:
            # DO NOT REMOVE THIS LINE
            # check the result of future, may raise a exception here
            result = f.result()
            get_logger().info("future result is %s", result)

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
