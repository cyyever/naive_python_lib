#!/usr/bin/env python3
import hashlib
import os
import pickle
import tempfile
from typing import Any, Callable


class DataStorage:
    """封装数据存储操作"""

    def __init__(self, data: Any = None, data_path: str | None = None):
        self.__data: Any = data
        self.__data_path: str | None = data_path
        self.__data_hash: str | None = None
        self.__fd: int | None = None
        self.__synced: bool = False

    def set_data_path(self, data_path: str) -> None:
        if self.__data_path == data_path:
            return
        if self.__data is None and self.__synced:
            self.__data = self.__load_data()
            self.__remove_data_file()
        self.__data_path = data_path
        self.__synced = False

    def set_data(self, data: Any) -> None:
        self.__data = data
        self.__data_hash = None
        self.__synced = False

    @property
    def data_path(self) -> str:
        if self.__data_path is None:
            self.__fd, self.__data_path = tempfile.mkstemp()
        return self.__data_path

    @property
    def data(self) -> Any:
        if not self.__synced or self.__data is not None:
            return self.__data
        self.__data = self.__load_data()
        return self.__data

    def __load_data(self) -> Any:
        assert self.__data_path
        with open(self.__data_path, "rb") as f:
            return pickle.load(f)

    def __remove_data_file(self) -> None:
        if self.__data_path is not None:
            if self.__fd is not None:
                os.close(self.__fd)
            os.remove(self.__data_path)
            self.__data_path = None

    @property
    def data_hash(self) -> str:
        if self.__data_hash is not None:
            return self.__data_hash
        hash_sha256 = hashlib.sha256()
        hash_sha256.update(pickle.dumps(self.data))
        self.__data_hash = hash_sha256.hexdigest()
        return self.__data_hash

    def clear(self) -> None:
        self.__remove_data_file()
        self.__data = None
        self.__data_hash = None
        self.__synced = False

    def save(self) -> None:
        if self.__data is not None and not self.__synced:
            with open(self.data_path, "wb") as f:
                pickle.dump(self.__data, f)
                self.__data = None
                self.__synced = True


def get_cached_data(path: str, data_fun: Callable) -> Any:
    def read_data():
        if not os.path.isfile(path):
            return None
        fd = os.open(path, flags=os.O_RDONLY)
        with os.fdopen(fd, "rb") as f:
            res = pickle.load(f)
        return res

    def write_data(data):
        fd = os.open(path, flags=os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "wb") as f:
            pickle.dump(data, f)

    data = read_data()
    if data is not None:
        return data
    data = data_fun()
    if data is None:
        raise RuntimeError("No data")
    write_data(data)
    return data
