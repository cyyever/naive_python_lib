from cyy_naive_lib.util import retry_operation


def test_retry_operation():
    def operation():
        return True, 3

    succ_flag, res = retry_operation(operation, 5, 1)
    assert succ_flag
    assert res == 3
