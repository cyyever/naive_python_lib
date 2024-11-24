import asyncio
import inspect
import traceback
from collections.abc import Callable
from typing import Any

from cyy_naive_lib.log import log_error


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
