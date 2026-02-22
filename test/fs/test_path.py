import shutil
from pathlib import Path

from cyy_naive_lib.fs.path import find_directories, list_files_by_suffixes
from cyy_naive_lib.fs.tempdir import TempDir


def test_list_files_by_suffixes() -> None:
    with TempDir():
        shutil.copy(__file__, ".")
        files = list_files_by_suffixes(Path.cwd(), [".py"])
        print(files)
        assert len(files) == 1
        assert Path(files[0]).name == Path(__file__).name
        (Path("foo") / "bar").mkdir(parents=True)
        dirs = find_directories(Path.cwd(), "bar")
        assert dirs
