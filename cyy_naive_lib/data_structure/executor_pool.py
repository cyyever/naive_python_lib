import asyncio
import concurrent.futures
import inspect
import traceback
from typing import Callable, List

from cyy_naive_lib.log import get_log_files, get_logger, set_file_handler


class ExecutorPool:
    def __init__(self, executor):
        self.__executor = executor
        self.__futures: List[concurrent.futures.Future] = []

    def wait(self, timeout=None) -> bool:
        done, not_done = concurrent.futures.wait(self.__futures, timeout=timeout)
        if not_done:
            return False
        return True

    def stop(self) -> list:
        self.wait()
        results: list = []
        for future in self.__futures:
            result = future.result()
            get_logger().debug("future result is %s", result)
            results.append(result)
        self.__executor.shutdown()
        return results

    @classmethod
    def _fun_wrapper(cls, fn, *args, **kwargs):
        for log_file in kwargs.pop("log_files", []):
            set_file_handler(log_file)
        try:
            if inspect.iscoroutinefunction(fn):
                return asyncio.run(fn(*args, **kwargs))
            return fn(*args, **kwargs)
        except Exception as e:
            get_logger().error("catch exception:%s", e)
            get_logger().error("traceback:%s", traceback.format_exc())
            return None

    def submit(self, fn: Callable, *args, **kwargs):
        kwargs = self.__add_kwargs(kwargs)
        future = self.__executor.submit(ExecutorPool._fun_wrapper, fn, *args, **kwargs)
        self.__futures.append(future)
        return future

    def exec(self, fn: Callable, *args, **kwargs):
        kwargs = self.__add_kwargs(kwargs)
        self.__futures.append(
            self.__executor.submit(ExecutorPool._fun_wrapper, fn, *args, **kwargs)
        )

    def _repeated_exec(
        self, stop_event, wait_time: float, fn: Callable, *args, **kwargs
    ):
        kwargs = self.__add_kwargs(kwargs)

        def worker():
            while True:
                ExecutorPool._fun_wrapper(fn, *args, **kwargs)
                if stop_event.wait(wait_time):
                    break

        self.__futures.append(self.__executor.submit(worker))

    def __add_kwargs(self, kwargs: dict):
        if "log_files" not in kwargs:
            kwargs["log_files"] = get_log_files()
        return kwargs
