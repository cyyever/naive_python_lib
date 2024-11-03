from collections.abc import Callable, Generator, Sequence
from typing import Any


def split_list_to_chunks(my_list: list, chunk_size: int) -> Generator:
    r"""
    Return a sequence of chunks
    """
    return (
        my_list[offs : offs + chunk_size] for offs in range(0, len(my_list), chunk_size)
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


def search_sublists(sublists: list[list]) -> Callable:
    assert sublists
    lookup_table: dict[tuple, Any] = {}
    for sub_list in sublists:
        assert sub_list
        a = sub_list[0]
        if a not in lookup_table:
            lookup_table[a] = set()
        lookup_table[a].add(tuple(sub_list))

    def search_sublists_impl(lst: list) -> dict[list, int]:
        result: dict = {}
        for idx, e in enumerate(lst):
            possible_sublists = lookup_table.get(e)
            if possible_sublists is None:
                continue
            for possible_sublist in possible_sublists:
                if tuple(lst[idx : idx + len(possible_sublist)]) == tuple(
                    possible_sublist
                ):
                    if possible_sublist not in result:
                        result[possible_sublist] = []
                    result[possible_sublist].append(idx)
        return result

    return search_sublists_impl


def sublist(a: list, b: list, start=0) -> int | None:
    idx = start
    while True:
        try:
            idx = a.index(b[0], idx)
            if a[idx : idx + len(b)] == b:
                return idx
            idx += 1
        except ValueError:
            break
    return None


def flatten_seq(seq: Sequence) -> list:
    r"""
    Flatten Return a flatted sequence
    """
    res = []
    for x in seq:
        if isinstance(x, list | tuple):
            res += flatten_seq(x)
        else:
            res.append(x)
    return res
