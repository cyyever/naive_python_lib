from time_counter import TimeCounter


def test_time_counter():
    with TimeCounter():
        print("hello world")
