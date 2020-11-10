from typing import Generator


def split_list_to_chunks(my_list: list, chunk_size: int) -> Generator:
    r"""
    Return a sequence of chunks
    """
    return (my_list[offs: offs + chunk_size]
            for offs in range(0, len(my_list), chunk_size))


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
