import concurrent
import concurrent.futures
import functools
import uuid
from collections.abc import Callable
from typing import Any

from cyy_naive_lib.log import log_debug

from .call import exception_aware_call


class ExecutorWrapper(concurrent.futures.Executor):
    def __init__(self, executor: concurrent.futures.Executor) -> None:
        self._executor: concurrent.futures.Executor = executor
        self.__futures: list[concurrent.futures.Future] = []

    @property
    def executor(self) -> concurrent.futures.Executor:
        return self._executor

    def wrap_executor(self, wrapper_type: type) -> None:
        new_executor = wrapper_type(executor=self._executor)
        assert isinstance(new_executor, concurrent.futures.Executor)
        self._executor = new_executor

    def submit(
        self, fn: Callable, /, *args: Any, **kwargs: Any
    ) -> concurrent.futures.Future:
        """Submits a callable to be executed with the given arguments.

        Schedules the callable to be executed as fn(*args, **kwargs) and returns
        a Future instance representing the execution of the callable.

        Returns:
            A Future representing the given call.
        """
        future = self._executor.submit(fn, *args, **kwargs)
        self.__futures.append(future)
        return future

    def peek_results(
        self,
        timeout: float | None = None,
        return_when=concurrent.futures.FIRST_EXCEPTION,
    ) -> tuple:
        done_futures, not_done_futures = concurrent.futures.wait(
            self.__futures, timeout=timeout, return_when=return_when
        )
        for future in done_futures:
            result = future.result()
            log_debug("future result is %s", result)
        return done_futures, not_done_futures

    def wait_results(
        self,
        timeout: float | None = None,
        return_when=concurrent.futures.FIRST_EXCEPTION,
    ) -> tuple[dict, int]:
        if not self.__futures:
            return {}, 0
        done_futures, not_done_futures = self.peek_results(
            timeout=timeout, return_when=return_when
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
    __global_store: Any | None = None

    @functools.cached_property
    def name(self) -> str:
        return str(uuid.uuid4())

    def __wait_job(self, global_store) -> None:
        print("wait %s", self.name)
        while global_store.has(f"{self.name}_pending"):
            self.peek_results(timeout=0.1)
        global_store.store(f"{self.name}_pending", True)

    def set_global_store(self, global_store) -> None:
        self.__global_store = global_store

    @classmethod
    def __mark_job_launched(
        cls, blocking_submit_executor_name: str, global_store
    ) -> None:
        name = blocking_submit_executor_name
        print("mark %s", name)
        global_store.remove(f"{name}_pending")

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
            functools.partial(self._fun, fn),
            *args,
            **kwargs,
            blocking_submit_executor_name=self.name,
            global_store=global_store,
        )

    def submit_batch(self, fun: Callable, kwargs_list: list):
        batch_fun = getattr(self._executor, "submit_batch", None)
        assert batch_fun is not None
        return batch_fun(
            [functools.partial(fun, **kwargs_elem) for kwargs_elem in kwargs_list],
        )
