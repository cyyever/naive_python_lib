import time
import traceback
from collections.abc import Callable

from cyy_naive_lib.log import log_error


def retry_operation(
    operation: Callable, retry_times: int, retry_sleep_time: float, *args, **kwargs
) -> tuple[bool, None]:
    for _ in range(retry_times):
        try:
            res = operation(*args, **kwargs)
            if res[0]:
                return res
        # pylint: disable=broad-exception-caught
        except Exception as e:
            log_error("catch exception:%s", e)
            log_error("traceback:%s", traceback.format_exc())
        log_error("operation failed,retry after %s seconds", retry_sleep_time)
        time.sleep(retry_sleep_time)
    return False, None
