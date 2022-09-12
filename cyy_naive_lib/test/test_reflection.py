from cyy_naive_lib.reflection import get_kwarg_names


def test_get_kwarg_names():
    def test_fun(a, b: int = 1):
        pass

    assert get_kwarg_names(test_fun) == {"b", "a"}
