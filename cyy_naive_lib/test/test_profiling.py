from profiling import Profile


def test_profile():
    with Profile():
        print("hello world")
