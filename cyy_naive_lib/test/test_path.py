import tempfile
import os
import shutil
from path import list_files_by_suffixes
from tempdir import TempDir


def test_list_files_by_suffixes():
    with TempDir():
        shutil.copy(__file__, ".")
        files = list_files_by_suffixes(os.getcwd(), [".py"])
        print(files)
        assert len(files) == 1
        assert os.path.basename(files[0]) == os.path.basename(__file__)
