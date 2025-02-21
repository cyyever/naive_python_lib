import concurrent
import concurrent.futures
from collections.abc import Callable, Sequence
from typing import Any

import gevent.lock

from .process_pool import ProcessPool


class CoroutineExcutorMixin(concurrent.futures.Executor):
    def submit_batch(
        self, funs: Sequence[Callable], kwargs_list: Sequence[dict]
    ) -> concurrent.futures.Future:
        return self.submit(self.batch_fun, funs, kwargs_list)

    @classmethod
    def batch_fun(cls, funs, kwargs_list) -> list[Any]:
        assert funs
        coroutines = [
            gevent.spawn(fun, **kwargs) for fun, kwargs in zip(funs, kwargs_list, strict=False)
        ]
        gevent.joinall(coroutines, raise_error=True)
        return [g.value for g in coroutines]


class ProcessPoolWithCouroutine(ProcessPool, CoroutineExcutorMixin):
    pass
