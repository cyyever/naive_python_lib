import os

from cyy_naive_lib.storage import (DataStorage, get_cached_data,
                                   persistent_cache)


def test_storage():
    data = DataStorage(b"abc")
    assert data.data_path is not None
    assert data.data == b"abc"
    data.save()
    assert data.data == b"abc"
    assert data.data_hash is not None


def test_get_cached_data():
    @persistent_cache(path="./abc",cache_time=5)
    def compute() -> int:
        return 123

    res = compute()
    assert res == 123

    assert compute() == 123
    os.remove("./abc")
