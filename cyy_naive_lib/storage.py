#!/usr/bin/env python3
import hashlib
import os
import traceback
import tempfile
from cyy_naive_lib.log import get_logger


class DataStorage:
    """ 封装数据存储操作 """

    def __init__(self, data, data_path=None):
        assert isinstance(data, bytes)
        self.__data = data
        self.__data_path = data_path
        self.__data_hash = None
        self.__fd = None

    def __del__(self):
        self.clear()

    @property
    def data_path(self):
        if self.__data_path is None:
            self.__fd, self.__data_path = tempfile.mkstemp()
        return self.__data_path

    @property
    def data(self):
        if self.__data:
            return self.__data
        assert self.__data_path
        with open(self.__data_path, "rb") as f:
            self.__data = f.read()
            return self.__data

    @property
    def data_hash(self):
        if self.__data_hash:
            return self.__data_hash
        hash_sha256 = hashlib.sha256()
        hash_sha256.update(self.data)
        self.__data_hash = hash_sha256.hexdigest()
        return self.__data_hash

    def clear(self):
        if self.__data_path is not None:
            os.close(self.__fd)
            os.remove(self.__data_path)
        self.__data = None
        self.__data_path = None
        self.__data_hash = None

    def save(self):
        try:
            data_path = self.data_path
            if self.__fd is not None:
                os.lseek(self.__fd, 0, 0)
                os.write(self.__fd, self.__data)
                self.__data = None
                return True
            with open(data_path, "xb") as f:
                f.write(self.__data)
                self.__data = None
                return True
        except Exception as e:
            get_logger().error("catch exception:%s", e)
            get_logger().error("traceback:%s", traceback.format_exc())
            return False
