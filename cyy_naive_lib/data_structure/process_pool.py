import concurrent.futures

from cyy_naive_lib.log import get_logger_setting

from .executor_pool import ExecutorPool
from .process_initialization import default_initializer, reinitialize_logger


class ProcessPool(ExecutorPool):
    def __init__(self, mp_context=None, initializer=None, initargs=(), **kwargs):
        if not initargs:
            initargs = [{}]
        if "initializers" not in initargs[0]:
            initargs[0]["initializers"] = []
        if initializer is not None:
            initargs[0]["initializers"].insert(0, initializer)
        initargs[0]["initializers"].insert(0, reinitialize_logger)
        if "initargs" not in initargs[0]:
            initargs[0]["initargs"] = {}
        initargs[0]["initargs"]["__logger_setting"] = get_logger_setting()

        super().__init__(
            concurrent.futures.ProcessPoolExecutor(
                mp_context=mp_context,
                initializer=default_initializer,
                initargs=initargs,
                **kwargs
            )
        )
