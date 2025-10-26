from cyy_naive_lib.time_counter import TimeCounter


def test_time_counter() -> None:
    with TimeCounter():
        print("hello world")
