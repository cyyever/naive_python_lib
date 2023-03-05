import asyncio
import concurrent
import concurrent.futures
import inspect
import traceback
import warnings
from typing import Callable, List

from cyy_naive_lib.log import get_logger


class ExecutorPool(concurrent.futures._base.Executor):
    def __init__(self, executor: concurrent.futures._base.Executor):
        self.__executor = executor
        self.__futures: List[concurrent.futures.Future] = []

    def submit(self, fn, *args, **kwargs):
        """Submits a callable to be executed with the given arguments.

        Schedules the callable to be executed as fn(*args, **kwargs) and returns
        a Future instance representing the execution of the callable.

        Returns:
            A Future representing the given call.
        """
        future = self.__executor.submit(ExecutorPool._fun_wrapper, fn, *args, **kwargs)
        self.__futures.append(future)
        return future

    def wait_results(
        self, timeout=None, return_when=concurrent.futures._base.ALL_COMPLETED
    ) -> list:
        concurrent.futures.wait(
            self.__futures, timeout=timeout, return_when=return_when
        )
        results: list = []
        for future in self.__futures:
            result = future.result()
            get_logger().debug("future result is %s", result)
            results.append(result)
        self.__futures.clear()
        return results

    def wait(
        self, timeout=None, return_when=concurrent.futures._base.ALL_COMPLETED
    ) -> list:
        warnings.warn("replaced by wait_results", DeprecationWarning)
        return self.wait_results(timeout=timeout, return_when=return_when)

    def shutdown(self, wait=True, *, cancel_futures=False):
        self.__executor.shutdown(wait=wait, cancel_futures=cancel_futures)

    def stop(self) -> list:
        warnings.warn("replaced by shutdown", DeprecationWarning)
        return self.shutdown()

    @classmethod
    def _fun_wrapper(cls, fn, *args, **kwargs):
        try:
            if inspect.iscoroutinefunction(fn):
                return asyncio.run(fn(*args, **kwargs))
            return fn(*args, **kwargs)
        except Exception as e:
            get_logger().error("catch exception:%s", e)
            get_logger().error("traceback:%s", traceback.format_exc())
            return None

    def exec(self, fn: Callable, *args, **kwargs):
        warnings.warn("replaced by submit", DeprecationWarning)
        # kwargs = self.__add_kwargs(kwargs)
        self.__futures.append(
            self.__executor.submit(ExecutorPool._fun_wrapper, fn, *args, **kwargs)
        )

    def _repeated_exec(
        self, stop_event, wait_time: float, fn: Callable, *args, **kwargs
    ) -> None:
        def worker():
            while True:
                ExecutorPool._fun_wrapper(fn, *args, **kwargs)
                if stop_event.wait(wait_time):
                    break

        self.__futures.append(self.__executor.submit(worker))
