from cyy_naive_lib.storage import DataStorage


def test_storage():
    data = DataStorage(b"abc")
    assert data.data_path is not None
    assert data.data == b"abc"
    assert data.save()
    assert data.data == b"abc"
    assert data.data_hash is not None
