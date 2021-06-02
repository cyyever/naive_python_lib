import time
import traceback
from typing import Callable, Tuple
from typing import List
from cyy_naive_lib.log import get_logger


def retry_operation(operation: Callable,
                    retry_times: int,
                    retry_sleep_time: float,
                    *args,
                    **kwargs) -> Tuple[bool,
                                       None]:
    for _ in range(retry_times):
        try:
            res = operation(*args, **kwargs)
            if res[0]:
                return res
        except Exception as e:
            get_logger().error("catch exception:%s", e)
            get_logger().error("traceback:%s", traceback.format_exc())
        get_logger().error("operation failed,retry after %s seconds", retry_sleep_time)
        time.sleep(retry_sleep_time)
    return False, None


def readlines(file_path: str) -> List[str]:
    lines = []
    try:
        with open(file_path, "r") as f:
            lines += f.readlines()
    except Exception:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            lines += f.readlines()
    return lines
