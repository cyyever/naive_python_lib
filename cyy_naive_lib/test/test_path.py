import tempfile
import os
import shutil
from path import list_files_by_suffixes


def test_list_files_by_suffixes():
    pre_dir = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdirname:
        os.chdir(tmpdirname)
        shutil.copy(__file__, ".")
        files = list_files_by_suffixes(os.getcwd(), [".py"])
        print(files)
        assert len(files) == 1
        assert os.path.basename(files[0]) == os.path.basename(__file__)
    os.chdir(pre_dir)
