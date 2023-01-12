import os
import shutil

from cyy_naive_lib.fs.path import find_directories, list_files_by_suffixes
from cyy_naive_lib.fs.tempdir import TempDir


def test_list_files_by_suffixes():
    with TempDir():
        shutil.copy(__file__, ".")
        files = list_files_by_suffixes(os.getcwd(), [".py"])
        print(files)
        assert len(files) == 1
        assert os.path.basename(files[0]) == os.path.basename(__file__)
        os.makedirs(os.path.join("foo", "bar"))
        dirs = find_directories(os.getcwd(), "bar")
        assert dirs
