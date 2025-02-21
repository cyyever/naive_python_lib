import concurrent.futures
import functools
from collections.abc import Callable
from typing import Any

from cyy_naive_lib.log import get_logger_setting

from .executor_pool import ExecutorPool
from .process_context import ProcessContext
from .process_initialization import (
    default_initializer,
    get_process_data,
    reinitialize_logger,
)


class ExtentedProcessPoolExecutor(concurrent.futures.ProcessPoolExecutor):
    def __init__(
        self,
        initializer=None,
        initargs=None,
        use_logger: bool = True,
        pass_process_data: bool = False,
        **kwargs,
    ) -> None:
        real_initarg: dict = {}
        real_initarg["initializers"] = [initializer]
        real_initarg["initargs_list"] = [{} if initargs is None else initargs]
        if use_logger:
            real_initarg["initializers"].insert(0, reinitialize_logger)
            real_initarg["initargs_list"].insert(
                0, {"logger_setting": get_logger_setting()}
            )
        if "mp_context" not in kwargs:
            kwargs["mp_context"] = ProcessContext().get_ctx()
        if "max_tasks_per_child" not in kwargs:
            kwargs["max_tasks_per_child"] = 1

        super().__init__(
            initializer=default_initializer,
            initargs=(real_initarg,),
            **kwargs,
        )
        self.__pass_process_data = pass_process_data

    @classmethod
    def wrapped_fn(
        cls, fn: Callable, pass_process_data: bool, *args: Any, **kwargs: Any
    ) -> concurrent.futures.Future:
        process_data = {}
        if pass_process_data:
            process_data = get_process_data()
        return fn(*args, **kwargs, **process_data)

    def submit(
        self, fn: Callable, /, *args: Any, **kwargs: Any
    ) -> concurrent.futures.Future:
        assert "fn" not in kwargs
        return super().submit(
            functools.partial(self.wrapped_fn, fn, self.__pass_process_data),
            *args,
            **kwargs,
        )


class ProcessPool(ExecutorPool):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(ExtentedProcessPoolExecutor(**kwargs))
