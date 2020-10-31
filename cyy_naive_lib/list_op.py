from collections.abc import Sequence


def split_list_to_chunks(my_list: list, chunk_size: int):
    r"""
    Return a sequence of chunks
    """
    return (my_list[offs: offs + chunk_size]
            for offs in range(0, len(my_list), chunk_size))


def flatten_sequence(seq: Sequence):
    r"""
    Return a list
    """
    res = []
    for x in seq:
        if isinstance(x, Sequence):
            res += flatten_sequence(x)
        else:
            res.append(x)
    return res
