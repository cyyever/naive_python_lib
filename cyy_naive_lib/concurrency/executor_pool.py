import concurrent
import concurrent.futures
from collections.abc import Callable
from typing import Any

from cyy_naive_lib.log import log_debug

from .call import exception_aware_call


class ExecutorPool(concurrent.futures.Executor):
    def __init__(
        self, executor: concurrent.futures.Executor, catch_exception: bool = False
    ) -> None:
        self.__executor: concurrent.futures.Executor = executor
        self.__catch_exception = catch_exception
        self.__futures: list[concurrent.futures.Future] = []

    def catch_exception(self) -> None:
        self.__catch_exception = True

    @property
    def executor(self) -> concurrent.futures.Executor:
        return self.__executor

    def submit(
        self, fn: Callable, *args: Any, **kwargs: Any
    ) -> concurrent.futures.Future:
        """Submits a callable to be executed with the given arguments.

        Schedules the callable to be executed as fn(*args, **kwargs) and returns
        a Future instance representing the execution of the callable.

        Returns:
            A Future representing the given call.
        """
        if self.__catch_exception:
            future = self.executor.submit(exception_aware_call, fn, *args, **kwargs)
        else:
            future = self.executor.submit(fn, *args, **kwargs)
        self.__futures.append(future)
        return future

    def wait_results(
        self,
        timeout: float | None = None,
        return_when=concurrent.futures.ALL_COMPLETED,
    ) -> tuple[dict, int]:
        if not self.__futures:
            return {}, 0
        done_futures, not_done_futures = concurrent.futures.wait(
            self.__futures, timeout=timeout, return_when=return_when
        )
        results: dict = {}
        for future in done_futures:
            result = future.result()
            log_debug("future result is %s", result)
            results[future] = result
        self.__futures.clear()
        if not_done_futures:
            self.__futures = list(not_done_futures)
        return results, len(self.__futures)

    def shutdown(self, *args, **kwargs) -> None:
        self.executor.shutdown(*args, **kwargs)
