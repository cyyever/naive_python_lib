import time
import traceback
from log import get_logger


class TimeCounter:
    def __init__(self):
        self.start_ns = None
        self.reset_start_time()

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
        get_logger().info(
            "block [%s => %d] uses %s ms",
            with_block.filename,
            with_block.lineno,
            used_ms,
        )


if __name__ == "__main__":
    with TimeCounter() as c:
        print("hello world")
