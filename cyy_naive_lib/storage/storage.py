import hashlib
import os
import tempfile
import time
from collections.abc import Callable
from enum import IntEnum, auto
from pathlib import Path

import dill


class DataLocation(IntEnum):
    NoData = auto()
    Memory = auto()
    Disk = auto()


class SyncedDataStorage:
    """封装数据存储操作"""

    def __init__(
        self, data: object = None, data_path: str | Path | None = None
    ) -> None:
        self.__data: object = data
        self.__data_path: Path | None = (
            Path(data_path) if data_path is not None else None
        )
        self.__data_hash: str | None = None
        self.__data_location: DataLocation = DataLocation.NoData
        if data is not None:
            self.__data_location = DataLocation.Memory
        elif data_path is not None:
            self.__data_location = DataLocation.Disk
        self.__fd: int | None = None
        self.__use_tmp_file: bool = False

    def has_data(self) -> bool:
        return self.__data_location != DataLocation.NoData

    def set_data_path(self, data_path: str | Path) -> None:
        data_path = Path(data_path)
        if self.__data_path == data_path:
            return
        assert self.__data_location != DataLocation.Disk
        self.__data_path = data_path
        self.__use_tmp_file = False

    def set_data(self, data: object) -> None:
        self.__data = data
        self.mark_new_data()

    def mark_new_data(self) -> None:
        self.__data_hash = None
        self.__data_location = DataLocation.Memory

    @property
    def data_path(self) -> Path | None:
        return self.__data_path

    @property
    def data(self) -> object:
        if self.__data_location == DataLocation.Disk:
            self.__data = self.__load_data()
        return self.__data

    def __load_data(self) -> object:
        assert self.__data_path is not None
        with self.__data_path.open("rb") as f:
            return dill.load(f)

    def __close_data_file(self) -> None:
        if self.__data_path is not None:
            if self.__fd is not None:
                os.close(self.__fd)
            self.__fd = None

    def __remove_data_file(self) -> None:
        if self.__data_path is not None:
            if self.__data_path.is_file():
                self.__close_data_file()
                self.__data_path.unlink()
            self.__data_path = None

    def __getitem__(self, key: object) -> object:
        data = self.data
        return data[key]  # type: ignore[index]

    def __contains__(self, key: object) -> bool:
        data = self.data
        return key in data  # type: ignore[operator]

    def __del__(self) -> None:
        if self.__use_tmp_file:
            self.__remove_data_file()

    @property
    def data_hash(self) -> str:
        if self.__data_hash is not None:
            return self.__data_hash
        hash_sha256 = hashlib.sha256()
        hash_sha256.update(dill.dumps(self.data))
        self.__data_hash = hash_sha256.hexdigest()
        return self.__data_hash

    def clear(self) -> None:
        self.__remove_data_file()
        self.__data = None
        self.__data_hash = None
        self.__data_path = None
        self.__data_location = DataLocation.NoData

    def save(self) -> None:
        if self.__data_location == DataLocation.Memory:
            if self.__data_path is None:
                self.__fd, tmp_path = tempfile.mkstemp()
                self.__data_path = Path(tmp_path)
                os.close(self.__fd)
                self.__fd = None
                self.__use_tmp_file = True
            else:
                parent = self.__data_path.parent
                if parent != Path():
                    parent.mkdir(parents=True, exist_ok=True)
            assert self.__data_path is not None
            with self.__data_path.open("wb") as f:
                dill.dump(self.__data, f)
                self.__data = None
                self.__data_location = DataLocation.Disk


def persistent_cache(
    path: str | Path | None = None, cache_time: float | None = None
) -> Callable:
    def read_data(p: Path) -> object:
        if not p.is_file():
            return None
        if cache_time is not None and time.time() > cache_time + p.stat().st_mtime:
            return None
        fd = os.open(p, flags=os.O_RDONLY)
        with os.fdopen(fd, "rb") as f:
            res = dill.load(f)
        return res

    def write_data(data: object, p: Path) -> None:
        if p.is_file():
            p.unlink()
        fd = os.open(p, flags=os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "wb") as f:
            dill.dump(data, f)

    def wrap(fun: Callable) -> Callable:
        def wrap2(*args: object, **kwargs: object) -> object:
            cache_path: Path | None = Path(path) if path is not None else None
            if cache_path is None:
                raw = kwargs.get("cache_path")
                assert raw is not None
                cache_path = Path(raw)  # type: ignore[arg-type]
            assert cache_path is not None
            hash_sha256 = hashlib.sha256()
            if args:
                hash_sha256.update(dill.dumps(args))
            else:
                hash_sha256.update(dill.dumps([]))
            if kwargs:
                hash_sha256.update(dill.dumps(kwargs))
            else:
                hash_sha256.update(dill.dumps({}))
            if cache_path.is_file():
                cache_path.unlink()
            cache_path.mkdir(parents=True, exist_ok=True)
            new_path = cache_path / hash_sha256.hexdigest()
            data = read_data(new_path)
            if data is not None:
                return data
            data = fun(*args, **kwargs)
            write_data(data, new_path)
            return data

        return wrap2

    return wrap


def get_cached_data(path: str | Path, data_fun: Callable) -> object:
    return persistent_cache(path=path)(data_fun)()
