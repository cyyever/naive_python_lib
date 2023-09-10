import os
import tempfile
import time


def get_temp_dir():
    return tempfile.TemporaryDirectory(suffix=str(time.time_ns()))


class TempDir:
    def __init__(self) -> None:
        self.prev_dir = None
        self.temp_dir = None

    def __enter__(self):
        self.prev_dir = os.getcwd()
        self.temp_dir = get_temp_dir()
        path = self.temp_dir.__enter__()
        os.chdir(path)
        return path

    def __exit__(self, *args):
        os.chdir(self.prev_dir)
        return self.temp_dir.__exit__(*args)
