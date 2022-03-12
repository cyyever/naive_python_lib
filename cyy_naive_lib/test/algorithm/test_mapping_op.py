from cyy_naive_lib.algorithm.mapping_op import (
    change_mapping_keys, flatten_mapping, get_mapping_values_by_key_order)


def test_get_mapping_values_by_key_order():
    res = list(get_mapping_values_by_key_order({2: "b", 1: "a"}))
    assert res == ["a", "b"]


def test_change_mapping_keys():
    res = change_mapping_keys({2: "b", 1: "a"}, str)
    assert res == {"2": "b", "1": "a"}


def test_flatten_mapping():
    res = flatten_mapping({2: "b", 1: {1: "c", 2: "a"}})
    assert res == ["c", "a", "b"]
