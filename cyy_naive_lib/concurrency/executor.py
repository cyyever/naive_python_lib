import concurrent
import concurrent.futures
from collections.abc import Callable
from typing import Any


class ExecutorWrapper(concurrent.futures.Executor):
    def __init__(self, executor: concurrent.futures.Executor) -> None:
        self._executor: concurrent.futures.Executor = executor

    def submit(
        self, fn: Callable, /, *args: Any, **kwargs: Any
    ) -> concurrent.futures.Future:
        return self._executor.submit(fn, *args, **kwargs)

    def shutdown(self, *args, **kwargs) -> None:
        self._executor.shutdown(*args, **kwargs)
