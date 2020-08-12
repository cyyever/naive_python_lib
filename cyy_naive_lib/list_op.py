from typing import Callable


def split_list_to_chunks(my_list: list, chunk_size: int):
    return (my_list[offs: offs + chunk_size]
            for offs in range(0, len(my_list), chunk_size))


def dict_value_by_order(d: dict):
    r"""
    Return a generator giving the dictionary values by key order.
    """
    for k in sorted(d.keys()):
        yield d[k]


def change_dict_key(d: dict, f: Callable):
    r"""
    Return a new dictionary with keys changed
    """
    new_dict = dict()
    for k, v in d.items():
        new_k = f(k)
        assert new_k not in new_dict
        new_dict[new_k] = v
    return new_dict
