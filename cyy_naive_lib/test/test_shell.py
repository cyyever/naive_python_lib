import tempfile
import os
from shell_factory import exec_cmd


def test_exec_cmd():
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdirname:
        os.chdir(tmpdirname)
        _, res = exec_cmd("ls", throw=False)
        os.chdir(cwd)
        assert res == 0
