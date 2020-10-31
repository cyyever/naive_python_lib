from typing import Callable
from collections.abc import Mapping, MutableMapping


def get_mapping_values_by_order(d: Mapping):
    r"""
    Return a generator giving the values by key order.
    """
    for k in sorted(d.keys()):
        yield d[k]


def change_mapping_keys(
        d: MutableMapping,
        f: Callable,
        recursive: bool = False):
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


def flatten_mapping(d: Mapping):
    r"""
    Return a list with values ordered by keys and flatten it
    """

    res = list()
    for v in get_mapping_values_by_order(d):
        if isinstance(v, Mapping):
            res += flatten_mapping(v)
        else:
            res.append(v)
    return res
