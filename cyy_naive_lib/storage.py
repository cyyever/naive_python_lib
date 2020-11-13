#!/usr/bin/env python3
import hashlib
import os
import traceback
import tempfile
from cyy_naive_lib.log import get_logger


class DataStorage:
    """ 封装数据存储操作 """

    def __init__(self, data, data_path=None):
        self.__data = data
        self.__data_path = data_path
        self.__data_hash = None

    def __del__(self):
        self.clear()

    @property
    def data_path(self):
        if self.__data_path is None:
            self.__data_path = tempfile.mkstemp()[1]
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
            os.remove(self.data_path)
        self.__data = None
        self.__data_path = None
        self.__data_hash = None

    def save(self):
        try:
            with open(self.data_path, "xb") as f:
                f.write(self.data)
                return True
        except Exception as e:
            get_logger().error("catch exception:%s", e)
            get_logger().error("traceback:%s", traceback.format_exc())
            return False
