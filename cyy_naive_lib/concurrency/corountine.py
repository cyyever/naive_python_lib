import concurrent
import concurrent.futures
from collections.abc import Callable, Sequence
from typing import Any

import gevent.lock

from .executor import ExecutorWrapper
from .process_pool import ExtentedProcessPoolExecutor


class CoroutineExcutorMixin(concurrent.futures.Executor):
    def submit_batch(self, funs: Sequence[Callable]) -> concurrent.futures.Future:
        return self.submit(self.batch_fun, funs)

    @classmethod
    def batch_fun(cls, funs, *args, **kwargs) -> list[Any]:
        assert funs
        coroutines = [
            gevent.spawn(fun, *args, **kwargs, coroutine_index=idx)
            for idx, fun in enumerate(funs)
        ]
        gevent.joinall(coroutines, raise_error=True)
        return [g.value for g in coroutines]


class CoroutineExcutor(ExecutorWrapper, CoroutineExcutorMixin):
    def __init__(self, executor: concurrent.futures.Executor | None = None) -> None:
        if executor is None:
            executor = ExtentedProcessPoolExecutor()
        super().__init__(executor=executor)
