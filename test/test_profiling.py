from cyy_naive_lib.profiling import Profile


def test_profile():
    with Profile():
        print("hello world")
