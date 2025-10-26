from typing import Any

from cyy_naive_lib.reflection import get_kwarg_names


def test_get_kwarg_names() -> None:
    def test_fun(a: Any, b: int = 1) -> None:
        pass

    assert get_kwarg_names(test_fun) == {"b", "a"}
