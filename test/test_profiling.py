from cyy_naive_lib.profiling import Profile


def test_profile() -> None:
    with Profile():
        print("hello world")
