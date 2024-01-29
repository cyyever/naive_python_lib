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


def search_sublists(l: list, sublists: list[list]) -> dict:
    assert sublists
    lookup_table: dict = {}
    for sub_list in sublists:
        assert sub_list
        a = sub_list[0]
        if a not in lookup_table:
            lookup_table[a] = []
        lookup_table[a].append(sub_list)
    result: dict = {}
    for idx, e in enumerate(l):
        possible_sublists = lookup_table.get(e, None)
        if possible_sublists is None:
            continue
        for possible_sublist in possible_sublists:
            if l[idx: idx + len(possible_sublist)] == possible_sublist:
                if possible_sublist not in result:
                    result[possible_sublist] = []
                result[possible_sublist].append(idx)
    return result


def sublist(a, b, start=0) -> int | None:
    idx = start
    while True:
        try:
            idx = a.index(b[0], idx)
            if a[idx: idx + len(b)] == b:
                return idx
            idx += 1
        except BaseException:
            break
    return None


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
