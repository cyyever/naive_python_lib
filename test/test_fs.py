from pathlib import Path

from cyy_naive_lib.fs.path import list_files
from cyy_naive_lib.fs.ssd import is_ssd


def test_is_ssd() -> None:
    is_ssd("/")


def test_list_files() -> None:
    assert list_files(Path(__file__).parent)
