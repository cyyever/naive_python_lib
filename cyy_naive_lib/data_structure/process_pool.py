import concurrent.futures

from cyy_naive_lib.log import apply_logger_setting, get_logger_setting

from .executor_pool import ExecutorPool
from .process_initialization import default_initializer


def reinitialize_logger(__logger_setting, **kwargs):
    apply_logger_setting(__logger_setting)


class ProcessPool(ExecutorPool):
    def __init__(self, mp_context=None, initializer=None, initargs=(), **kwargs):
        if initializer is None:
            initargs = (
                [reinitialize_logger],
                {"__logger_setting": get_logger_setting()},
            )
        else:
            initargs[0] = [reinitialize_logger, initializer] + initargs[0]
            initargs[1]["__logger_setting"] = get_logger_setting()

        super().__init__(
            concurrent.futures.ProcessPoolExecutor(
                mp_context=mp_context,
                initializer=default_initializer,
                initargs=initargs,
                **kwargs
            )
        )
