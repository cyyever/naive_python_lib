import shutil

from cyy_naive_lib.fs.tempdir import TempDir
from cyy_naive_lib.storage import DataStorage, load_json, persistent_cache, save_json


def test_storage() -> None:
    data = DataStorage(b"abc")
    assert data.has_data()
    assert data.data == b"abc"
    data.save()
    assert data.data == b"abc"
    assert data.data_hash is not None
    data.set_data({1: 2, "c": "d"})
    assert data[1] == 2
    assert data["c"] == "d"


def test_json_io():
    data = {1: 2, "c": "d"}
    with TempDir():
        save_json(data, "./abc.json")
        data2 = load_json("./abc.json")
        assert len(data) == len(data2)


def test_get_cached_data() -> None:
    with TempDir():

        @persistent_cache(path="./abc", cache_time=5)
        def compute() -> int:
            return 123

        res = compute()
        assert res == 123

        assert compute() == 123
        shutil.rmtree("./abc")
