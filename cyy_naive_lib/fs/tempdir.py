import os
import tempfile
from pathlib import Path


class TempDir:
    def __init__(self) -> None:
        self.__prev_dir: Path | None = None
        self.__temp_dir: tempfile.TemporaryDirectory[str] | None = None

    def __enter__(self) -> str:
        self.__prev_dir = Path.cwd()
        self.__temp_dir = tempfile.TemporaryDirectory()
        path = self.__temp_dir.__enter__()
        os.chdir(path)
        return path

    def __exit__(self, *args: object) -> None:
        assert self.__prev_dir is not None
        assert self.__temp_dir is not None
        os.chdir(self.__prev_dir)
        self.__temp_dir.__exit__(*args)
