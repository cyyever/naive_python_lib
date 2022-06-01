#!/usr/bin/env python3
import hashlib
import os
import pickle
import tempfile
from typing import Any, Callable


class DataStorage:
    """封装数据存储操作"""

    def __init__(self, data: Any, data_path: str | None = None):
        assert data is not None
        self.__data = data
        self.__data_path = data_path
        self.__data_hash: str | None = None
        self.__fd = None
        self.__synced = False

    def __del__(self):
        self.clear()

    @property
    def data_path(self):
        if self.__data_path is None:
            self.__fd, self.__data_path = tempfile.mkstemp()
        return self.__data_path

    @property
    def data(self):
        if self.__data is not None:
            return self.__data
        assert self.__data_path
        with open(self.__data_path, "rb") as f:
            self.__data = pickle.load(f)
            return self.__data

    @property
    def data_hash(self) -> str:
        if self.__data_hash is not None:
            return self.__data_hash
        hash_sha256 = hashlib.sha256()
        hash_sha256.update(pickle.dumps(self.data))
        self.__data_hash = hash_sha256.hexdigest()
        return self.__data_hash

    def clear(self):
        if self.__data_path is not None:
            if self.__fd is not None:
                os.close(self.__fd)
            os.remove(self.__data_path)
        self.__data = None
        self.__data_path = None
        self.__data_hash = None

    def save(self):
        if self.__data is not None and not self.__synced:
            with open(self.data_path, "wb") as f:
                pickle.dump(self.__data, f)
                self.__data = None


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
