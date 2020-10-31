from typing import Callable


def dict_value_by_order(d: dict):
    r"""
    Return a generator giving the dictionary values by key order.
    """
    for k in sorted(d.keys()):
        yield d[k]


def change_dict_key(d: dict, f: Callable, recursive: bool = False):
    r"""
    Return a new dictionary with keys changed
    """
    new_dict = dict()
    for k, v in d.items():
        if recursive and isinstance(v, dict):
            v = change_dict_key(v, f)
        new_k = f(k)
        assert new_k not in new_dict
        new_dict[new_k] = v
    return new_dict


def dict_to_list(d: dict):
    r"""
    Return a list with values ordered by keys
    """
    res = list()
    for k in sorted(d.keys()):
        v = d[k]
        if isinstance(v, dict):
            v = dict_to_list(v)
        res.append(v)
    return res
