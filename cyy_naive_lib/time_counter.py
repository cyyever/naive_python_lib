import time
import traceback

from cyy_naive_lib.log import get_logger


class TimeCounter:
    def __init__(
        self, debug_logging=True, with_block_logging=True, log_prefix: str = None
    ):
        self.debug_logging = debug_logging
        self.with_block_logging = with_block_logging
        self.__log_prefix = log_prefix
        self.start_ns = None
        self.reset_start_time()

    def enable_with_block_logging(self):
        self.with_block_logging = True

    def disable_with_block_logging(self):
        self.with_block_logging = False

    def reset_start_time(self):
        self.start_ns = time.monotonic_ns()

    def elapsed_milliseconds(self):
        return (time.monotonic_ns() - self.start_ns) / 1000000

    def __enter__(self):
        self.reset_start_time()
        return self

    def __exit__(self, exc_type, exc_value, real_traceback):
        if real_traceback:
            return
        used_ms = self.elapsed_milliseconds()
        with_block = traceback.extract_stack(limit=2)[0]

        if self.debug_logging:
            logging_func = get_logger().debug
        else:
            logging_func = get_logger().info
        logging_func(
            "%s [%s => %d] uses %s ms",
            self.__log_prefix if self.__log_prefix is not None else "",
            with_block.filename,
            with_block.lineno,
            used_ms,
        )
