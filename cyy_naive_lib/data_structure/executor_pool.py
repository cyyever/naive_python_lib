import asyncio
import concurrent
import concurrent.futures
import inspect
import traceback
from typing import Any, Callable, List

from cyy_naive_lib.log import get_logger


class ExecutorPool(concurrent.futures.Executor):
    def __init__(self, executor: concurrent.futures.Executor) -> None:
        self.__executor: concurrent.futures.Executor = executor
        self.__futures: List[concurrent.futures.Future] = []

    def submit(
        self, fn: Callable, *args: Any, **kwargs: Any
    ) -> concurrent.futures.Future:
        """Submits a callable to be executed with the given arguments.

        Schedules the callable to be executed as fn(*args, **kwargs) and returns
        a Future instance representing the execution of the callable.

        Returns:
            A Future representing the given call.
        """
        future = self.__executor.submit(self._fun_wrapper, fn, *args, **kwargs)
        self.__futures.append(future)
        return future

    def wait_results(
        self,
        timeout: float | None = None,
        return_when=concurrent.futures.ALL_COMPLETED,
    ) -> tuple:
        done_futures, not_done_futures = concurrent.futures.wait(
            self.__futures, timeout=timeout, return_when=return_when
        )
        results: dict = {}
        for future in done_futures:
            result = future.result()
            get_logger().debug("future result is %s", result)
            results[future] = result
        return results, not_done_futures

    def shutdown(self, wait: bool = True, *, cancel_futures=False) -> None:
        self.__executor.shutdown(wait=wait, cancel_futures=cancel_futures)

    @classmethod
    def _fun_wrapper(cls, fn: Callable, *args: Any, **kwargs: Any) -> Any:
        try:
            if inspect.iscoroutinefunction(fn):
                return asyncio.run(fn(*args, **kwargs))
            return fn(*args, **kwargs)
        # pylint: disable=broad-exception-caught
        except Exception as e:
            get_logger().error("catch exception:%s", e)
            get_logger().error("traceback:%s", traceback.format_exc())
            return None

    def _repeated_exec(
        self, stop_event: Any, wait_time: float, fn: Callable, *args: Any, **kwargs: Any
    ) -> None:
        def worker():
            while True:
                ExecutorPool._fun_wrapper(fn, *args, **kwargs)
                if stop_event.wait(wait_time):
                    break

        self.__futures.append(self.__executor.submit(worker))
