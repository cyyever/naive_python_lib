from mapping_op import get_mapping_values_by_order, change_mapping_keys, flatten_mapping


def test_get_mapping_values_by_order():
    res = list(get_mapping_values_by_order({2: "b", 1: "a"}))
    assert res == ["a", "b"]


def test_change_mapping_keys():
    res = change_mapping_keys({2: "b", 1: "a"}, str)
    assert res == {"2": "b", "1": "a"}


def test_flatten_mapping():
    res = flatten_mapping({2: "b", 1: {1: "c", 2: "a"}})
    assert res == ["c", "a", "b"]
