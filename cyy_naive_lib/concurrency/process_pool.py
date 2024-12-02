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


class ProcessPool(ExecutorPool):
    def __init__(
        self,
        initializer=None,
        initargs=None,
        use_logger: bool = True,
        pass_process_data: bool = False,
        max_tasks_per_child: int | None = 1,
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

        super().__init__(
            concurrent.futures.ProcessPoolExecutor(
                initializer=default_initializer,
                initargs=(real_initarg,),
                **kwargs,
                max_tasks_per_child=max_tasks_per_child,
            )
        )
        self.__pass_process_data = pass_process_data

    @classmethod
    def wrap_fun(cls, fn: Callable, *args: Any, **kwargs: Any) -> Any:
        return fn(*args, **kwargs, **get_process_data())

    def submit(
        self, fn: Callable, *args: Any, **kwargs: Any
    ) -> concurrent.futures.Future:
        if self.__pass_process_data:
            return super().submit(
                functools.partial(self.wrap_fun, fn),
                *args,
                **kwargs,
            )

        return super().submit(fn, *args, **kwargs)
