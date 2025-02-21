import concurrent
import concurrent.futures
import functools
import time
import uuid
from collections.abc import Callable
from typing import Any

from .call import exception_aware_call


class ExecutorWrapper(concurrent.futures.Executor):
    def __init__(self, executor: concurrent.futures.Executor) -> None:
        self._executor: concurrent.futures.Executor = executor

    @property
    def executor(self):
        return self._executor

    def wrap_executor(self, wrapper_type: type) -> None:
        new_executor = wrapper_type(executor=self._executor)
        assert isinstance(new_executor, concurrent.futures.Executor)
        self._executor = new_executor

    def submit(
        self, fn: Callable, /, *args: Any, **kwargs: Any
    ) -> concurrent.futures.Future:
        return self._executor.submit(fn, *args, **kwargs)

    def shutdown(self, *args, **kwargs) -> None:
        self._executor.shutdown(*args, **kwargs)


class ExceptionSafeExecutor(ExecutorWrapper):
    catch_exception: bool = False

    def submit(
        self, fn: Callable, /, *args: Any, **kwargs: Any
    ) -> concurrent.futures.Future:
        """Submits a callable to be executed with the given arguments.

        Schedules the callable to be executed as fn(*args, **kwargs) and returns
        a Future instance representing the execution of the callable.

        Returns:
            A Future representing the given call.
        """
        if self.catch_exception:
            return super().submit(exception_aware_call, fn, *args, **kwargs)
        return super().submit(fn, *args, **kwargs)


class BlockingSubmitExecutor(ExecutorWrapper):
    __thread_store: dict | None = None
    __global_store: Any | None = None

    @functools.cached_property
    def name(self) -> str:
        return str(uuid.uuid4())

    def __wait_job(self, global_store) -> None:
        while global_store.has(f"{self.name}_pending"):
            time.sleep(0.1)
        global_store.store(f"{self.name}_pending", True)

    def set_global_store(self, global_store) -> None:
        self.__global_store = global_store

    @classmethod
    def __mark_job_launched(
        cls, blocking_submit_executor_name: str, global_store
    ) -> None:
        name = blocking_submit_executor_name
        if cls.__thread_store is None:
            cls.__thread_store = {}
        assert cls.__thread_store is not None
        if f"{name}_pending" not in cls.__thread_store:
            global_store.remove(f"{name}_pending")
            cls.__thread_store[f"{name}_pending"] = True

    @classmethod
    def _fun(cls, fun: Callable, *args, **kwargs):
        cls.__mark_job_launched(
            kwargs.pop("blocking_submit_executor_name"), kwargs.pop("global_store")
        )
        return fun(*args, **kwargs)

    def submit(
        self, fn: Callable, /, *args: Any, **kwargs: Any
    ) -> concurrent.futures.Future:
        global_store = self.__global_store
        self.__wait_job(global_store)
        return super().submit(
            fn,
            *args,
            **kwargs,
            blocking_submit_executor_name=self.name,
            global_store=global_store,
        )

    def submit_batch(self, fun: Callable, kwargs_list: list):
        assert hasattr(super(), "submit_batch")
        return super().submit_batch(
            [functools.partial(fun, **kwargs_elem) for kwargs_elem in kwargs_list],
        )
