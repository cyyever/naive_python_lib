from storage import DataStorage


def test_storage():
    data = DataStorage("abc")
    assert data.data_path is not None
    assert data.data == "abc"
