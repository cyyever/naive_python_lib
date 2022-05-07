import os

from cyy_naive_lib.storage import DataStorage, get_cached_data


def test_storage():
    data = DataStorage(b"abc")
    assert data.data_path is not None
    assert data.data == b"abc"
    assert data.save()
    assert data.data == b"abc"
    assert data.data_hash is not None


def test_get_cached_data():
    assert get_cached_data(path="./abc", data_fun=lambda: "123") == "123"
    os.remove("./abc")
