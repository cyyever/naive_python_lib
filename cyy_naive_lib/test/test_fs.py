from ..fs.ssd import is_ssd


def test_is_ssd() -> None:
    is_ssd("/")
