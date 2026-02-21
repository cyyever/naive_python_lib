from collections.abc import Callable, Generator, Iterable, Sequence
from itertools import batched
from typing import Any


def split_list_to_chunks(
    my_list: list[Any], chunk_size: int
) -> Generator[list[Any], None, None]:
    r"""
    Return a sequence of chunks
    """
    return (list(batch) for batch in batched(my_list, chunk_size))


def flatten_list(seq: list[Any]) -> list[Any]:
    r"""
    Return a list
    """
    res: list[Any] = []
    for x in seq:
        if isinstance(x, list):
            res += flatten_list(x)
        else:
            res.append(x)
    return res


def search_sublists(
    sublists: Sequence[Sequence[Any]],
) -> Callable[[list[Any]], dict[tuple[Any, ...], list[int]]]:
    assert sublists
    lookup_table: dict[Any, set[tuple[Any, ...]]] = {}
    for sub_list in sublists:
        assert sub_list
        a = sub_list[0]
        if a not in lookup_table:
            lookup_table[a] = set()
        lookup_table[a].add(tuple(sub_list))

    def search_sublists_impl(
        lst: list[Any],
    ) -> dict[tuple[Any, ...], list[int]]:
        result: dict[tuple[Any, ...], list[int]] = {}
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


def sublist[T](a: Sequence[T], b: Sequence[T], start: int = 0) -> int | None:
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


def flatten_seq(seq: Iterable[Any]) -> list[Any]:
    r"""
    Flatten Return a flatted sequence
    """
    res: list[Any] = []
    for x in seq:
        if isinstance(x, list | tuple):
            res += flatten_seq(x)
        else:
            res.append(x)
    return res
