import time


class TimeCounter:
    def __init__(self):
        self.start_ns = None

    def reset_start_time(self):
        self.start_ns = time.monotonic_ns()

    def elapsed_milliseconds(self):
        return (time.monotonic_ns() - self.start_ns) / 1000000

    def __enter__(self):
        self.reset_start_time()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass
