import concurrent.futures
import functools
from collections.abc import Callable

from .executor import ExecutorWrapper
from .process_context import ProcessContext
from .process_initialization import (
    get_process_data,
    make_initializer,
)


class ExtendedProcessPoolExecutor(concurrent.futures.ProcessPoolExecutor):
    def __init__(
        self,
        initializer: None | Callable = None,
        initargs: dict | None = None,
        **kwargs,
    ) -> None:
        real_initarg: dict = {}
        real_initarg["initializers"] = [initializer]
        real_initarg["initargs_list"] = [{} if initargs is None else initargs]
        pass_process_data = "process_data" in real_initarg["initargs_list"][0]
        if "mp_context" not in kwargs:
            kwargs["mp_context"] = ProcessContext().get_ctx()
        if "max_tasks_per_child" not in kwargs:
            kwargs["max_tasks_per_child"] = 1

        init_func, wrap_initargs = make_initializer()
        super().__init__(
            initializer=init_func,
            initargs=wrap_initargs(real_initarg),
            **kwargs,
        )
        self.__pass_process_data = pass_process_data

    @classmethod
    def wrapped_fn(
        cls, fn: Callable, pass_process_data: bool, *args: object, **kwargs: object
    ) -> concurrent.futures.Future:
        process_data = {}
        if pass_process_data:
            process_data = get_process_data()
        return fn(*args, **kwargs, **process_data)

    def submit(  # type: ignore[override]
        self, fn: Callable, /, *args: object, **kwargs: object
    ) -> concurrent.futures.Future:
        assert "fn" not in kwargs
        return super().submit(
            functools.partial(self.wrapped_fn, fn, self.__pass_process_data),
            *args,
            **kwargs,
        )


class ProcessPool(ExecutorWrapper):
    def __init__(self, **kwargs) -> None:
        super().__init__(ExtendedProcessPoolExecutor(**kwargs))
