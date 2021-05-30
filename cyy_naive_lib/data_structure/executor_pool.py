import asyncio
import concurrent.futures
import inspect
import traceback
from typing import Callable, List

from log import get_logger


class ExecutorPool:
    def __init__(self, executor):
        self.__executor = executor
        self.__futures: List[concurrent.futures.Future] = []

    def stop(self):
        concurrent.futures.wait(self.__futures)
        for f in self.__futures:
            # DO NOT REMOVE THIS LINE
            # check the result of future, may raise a exception here
            result = f.result()
            get_logger().debug("future result is %s", result)

    @staticmethod
    def process_once(fn, *args, **kwargs):
        try:
            if inspect.iscoroutinefunction(fn):
                asyncio.run(fn(*args, **kwargs))
            else:
                fn(*args, **kwargs)
        except Exception as e:
            get_logger().error("catch exception:%s", e)
            get_logger().error("traceback:%s", traceback.format_exc())

    def exec(self, fn: Callable, *args, **kwargs):
        self.__futures.append(
            self.__executor.submit(ExecutorPool.process_once, fn, *args, **kwargs)
        )

    def _repeated_exec(
        self, stop_event, wait_time: float, fn: Callable, *args, **kwargs
    ):
        def worker():
            while True:
                ExecutorPool.process_once(fn, *args, **kwargs)
                if stop_event.wait(wait_time):
                    break

        self.__futures.append(self.__executor.submit(worker))
