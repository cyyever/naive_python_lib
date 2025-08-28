import asyncio
import copy
import inspect
import time
import traceback
from collections.abc import Callable
from typing import Any, Self

from cyy_naive_lib.log import log_error


class Expected[T]:
    def __init__(self, *, ok: bool, value: T | None) -> None:
        """
        Like C++ std::expected

        """
        assert (ok and value is not None) or (not ok and value is None)
        self.__ok: bool = ok
        self.__value: None | tuple[T] = value if value is None else (value,)

    @classmethod
    def ok(cls, value: T):
        return cls(ok=True, value=value)

    @classmethod
    def not_ok(cls):
        return cls(ok=False, value=None)

    def is_ok(self) -> bool:
        return self.__ok

    def value(self) -> T:
        assert self.__ok
        assert self.__value is not None
        return self.__value[0]


class Decorator[T]:
    def __init__(self, obj: T) -> None:
        self._decorator_object = obj
        # self.__class__ = obj.__class__

    def __copy__(self) -> Self:
        return type(self)(copy.copy(self._decorator_object))

    def __getattr__(self, name: str) -> Any:
        if "decorator_object" in name:
            raise AttributeError()
        return getattr(self._decorator_object, name)


def exception_aware_call(fn: Callable, *args: Any, **kwargs: Any) -> Any:
    try:
        if inspect.iscoroutinefunction(fn):
            return asyncio.run(fn(*args, **kwargs))
        return fn(*args, **kwargs)
    # pylint: disable=broad-exception-caught
    except Exception as e:
        log_error("catch exception:%s", e)
        log_error("traceback:%s", traceback.format_exc())
    return None


def retry_operation(
    operation: Callable[..., Expected],
    retry_times: int,
    retry_sleep_time: float,
    *args,
    **kwargs,
) -> tuple[bool, None]:
    for _ in range(retry_times):
        try:
            res = operation(*args, **kwargs)
            if res.is_ok():
                return res.value()
            continue
        # pylint: disable=broad-exception-caught
        except Exception as e:
            log_error("catch exception:%s", e)
            log_error("traceback:%s", traceback.format_exc())
        log_error("operation failed,retry after %s seconds", retry_sleep_time)
        time.sleep(retry_sleep_time)
    return False, None
