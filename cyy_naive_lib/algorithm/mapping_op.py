from collections.abc import (
    Callable,
    Generator,
    Mapping,
    MutableMapping,
    Sequence,
)
from typing import Any

from ..function import Expected
from .generic import recursive_mutable_op


def get_mapping_items_by_key_order(
    d: Mapping[Any, Any],
) -> Generator[tuple[Any, Any], None, None]:
    r"""
    Return a generator giving the items by key order.
    """
    for k in sorted(d.keys()):
        yield (k, d[k])


def mapping_to_list(d: Mapping[str, Any]) -> list[dict[str, Any]]:
    keys = list(d.keys())
    transposed_values = zip(*d.values(), strict=True)
    return [dict(zip(keys, row, strict=True)) for row in transposed_values]


def get_mapping_values_by_key_order(
    d: Mapping[Any, Any],
) -> Generator[Any, None, None]:
    r"""
    Return a generator giving the values by key order.
    """
    for _, v in get_mapping_items_by_key_order(d):
        yield v


def change_mapping_keys(
    d: MutableMapping[Any, Any],
    f: Callable[[object], object],
    recursive: bool = False,
) -> MutableMapping[Any, Any]:
    r"""
    Return a new mapping with keys changed
    """
    new_d = type(d)()
    for k, v in d.items():
        new_v = change_mapping_keys(v, f, recursive) if recursive and isinstance(v, MutableMapping) else v
        new_k = f(k)
        assert new_k not in new_d
        new_d[new_k] = new_v
    return new_d


def change_mapping_values[T, S](
    d: T, key: S, f: Callable[[S], object]
) -> T | list[Any]:
    r"""
    Return a new mapping with values changed
    """

    def fun(data: object) -> Expected:
        if isinstance(data, MutableMapping) and key in data:
            data[key] = f(data[key])
            return Expected.ok(data)
        return Expected.not_ok()

    return recursive_mutable_op(d, fun, check=True)


def flatten_mapping(d: Mapping[Any, Any]) -> list[Any]:
    r"""
    Return a list with values ordered by keys and flatten it
    """

    res: list[Any] = []
    for v in get_mapping_values_by_key_order(d):
        if isinstance(v, Mapping):
            res += flatten_mapping(v)
        else:
            res.append(v)
    return res


def reduce_values_by_key(
    f: Callable[[list[Any]], Any], maps: Sequence[dict[str, Any]]
) -> dict[str, Any]:
    value_seq_dict: dict[str, list[Any]] = {k: [] for k in maps[0]}
    for m in maps:
        for k, v in m.items():
            value_seq_dict[k].append(v)
    return {k: f(v) for k, v in value_seq_dict.items()}
