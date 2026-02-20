from collections.abc import (
    Callable,
    Generator,
    Mapping,
    MutableMapping,
    Sequence,
)

from ..function import Expected
from .generic import recursive_mutable_op


def get_mapping_items_by_key_order(d: Mapping) -> Generator:
    r"""
    Return a generator giving the items by key order.
    """
    for k in sorted(d.keys()):
        yield (k, d[k])


def mapping_to_list(d: Mapping) -> list[dict]:
    keys = list(d.keys())
    transposed_values = zip(*d.values(), strict=True)
    return [dict(zip(keys, row, strict=True)) for row in transposed_values]


def get_mapping_values_by_key_order(d: Mapping) -> Generator:
    r"""
    Return a generator giving the values by key order.
    """
    for _, v in get_mapping_items_by_key_order(d):
        yield v


def change_mapping_keys(
    d: MutableMapping, f: Callable[[object], object], recursive: bool = False
) -> MutableMapping:
    r"""
    Return a new mapping with keys changed
    """
    new_d = type(d)()
    for k, v in d.items():
        if recursive and isinstance(v, MutableMapping):
            v = change_mapping_keys(v, f, recursive)
        new_k = f(k)
        assert new_k not in new_d
        new_d[new_k] = v
    return new_d


def change_mapping_values[T, S](d: T, key: S, f: Callable[[S], object]) -> T | list:
    r"""
    Return a new mapping with values changed
    """

    def fun(data):
        if isinstance(data, MutableMapping) and key in data:
            data[key] = f(data[key])
            return Expected.ok(data)
        return Expected.not_ok()

    return recursive_mutable_op(d, fun, check=True)


def flatten_mapping(d: Mapping) -> list:
    r"""
    Return a list with values ordered by keys and flatten it
    """

    res = []
    for v in get_mapping_values_by_key_order(d):
        if isinstance(v, Mapping):
            res += flatten_mapping(v)
        else:
            res.append(v)
    return res


def reduce_values_by_key(f: Callable, maps: Sequence[dict]) -> dict:
    value_seq_dict: dict = {k: [] for k in maps[0]}
    for m in maps:
        for k, v in m.items():
            value_seq_dict[k].append(v)
    return {k: f(v) for k, v in value_seq_dict.items()}
