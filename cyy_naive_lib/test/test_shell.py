from shell_factory import exec_cmd


def test_exec_cmd():
    _, res = exec_cmd("ls", throw=False)
    assert res == 0
