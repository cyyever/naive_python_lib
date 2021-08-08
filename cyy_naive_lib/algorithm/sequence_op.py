from typing import Generator, Sequence


def split_list_to_chunks(my_list: list, chunk_size: int) -> Generator:
    r"""
    Return a sequence of chunks
    """
    return (
        my_list[offs: offs + chunk_size] for offs in range(0, len(my_list), chunk_size)
    )


def flatten_list(seq: list) -> list:
    r"""
    Return a list
    """
    res = []
    for x in seq:
        if isinstance(x, list):
            res += flatten_list(x)
        else:
            res.append(x)
    return res


def flatten_seq(seq: Sequence) -> list:
    r"""
    Flatten Return a flatted sequence
    """
    res = []
    for x in seq:
        if isinstance(x, (list, tuple)):
            res += flatten_seq(x)
        else:
            res.append(x)
    return res
