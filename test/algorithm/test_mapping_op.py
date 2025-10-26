from cyy_naive_lib.algorithm.mapping_op import (
    change_mapping_keys,
    change_mapping_values,
    flatten_mapping,
    get_mapping_values_by_key_order,
    reduce_values_by_key,
)


def test_get_mapping_values_by_key_order() -> None:
    res = list(get_mapping_values_by_key_order({2: "b", 1: "a"}))
    assert res == ["a", "b"]


def test_change_mapping_keys() -> None:
    res = change_mapping_keys({2: "b", 1: "a"}, str)
    assert res == {"2": "b", "1": "a"}


def test_change_mapping_values() -> None:
    res = change_mapping_values({2: "b", 1: "a"}, 2, lambda v: v + "c")
    assert res == {2: "bc", 1: "a"}
    res = change_mapping_values([{2: "b", 1: "a"}], 2, lambda v: v + "c")
    assert res == [{2: "bc", 1: "a"}]


def test_flatten_mapping() -> None:
    res = flatten_mapping({2: "b", 1: {1: "c", 2: "a"}})
    assert res == ["c", "a", "b"]


def test_reduce_values_by_key() -> None:
    res = reduce_values_by_key(f=len, maps=[{"a": 1, "b": 2}, {"a": 2, "b": 3}])
    assert res == {"a": 2, "b": 2}
    res = reduce_values_by_key(f=sum, maps=[{"a": 1, "b": 2}, {"a": 2, "b": 3}])
    assert res == {"a": 3, "b": 5}
