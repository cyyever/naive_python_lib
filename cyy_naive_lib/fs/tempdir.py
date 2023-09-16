import os
import tempfile
import time


def get_temp_dir() -> tempfile.TemporaryDirectory:
    return tempfile.TemporaryDirectory(suffix=str(time.time_ns()))


class TempDir:
    def __init__(self) -> None:
        self.__prev_dir: None | str = None
        self.__temp_dir: None | tempfile.TemporaryDirectory = None

    def __enter__(self) -> str:
        self.__prev_dir = os.getcwd()
        self.__temp_dir = get_temp_dir()
        path = self.__temp_dir.__enter__()
        os.chdir(path)
        return path

    def __exit__(self, *args) -> None:
        assert self.__prev_dir is not None
        assert self.__temp_dir is not None
        os.chdir(self.__prev_dir)
        self.__temp_dir.__exit__(*args)
