import shutil

from cyy_naive_lib.fs.tempdir import TempDir
from cyy_naive_lib.storage import DataStorage, persistent_cache


def test_storage():
    data = DataStorage(b"abc")
    assert data.data == b"abc"
    data.save()
    assert data.data == b"abc"
    assert data.data_hash is not None


def test_get_cached_data():
    with TempDir():

        @persistent_cache(path="./abc", cache_time=5)
        def compute() -> int:
            return 123

        res = compute()
        assert res == 123

        assert compute() == 123
        shutil.rmtree("./abc")
