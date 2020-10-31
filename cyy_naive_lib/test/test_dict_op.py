from dict_op import dict_value_by_order, change_dict_key


def test_dict_value_by_order():
    res = list(dict_value_by_order({2: "b", 1: "a"}))
    assert res == ["a", "b"]


def test_change_dict_key():
    res = change_dict_key({2: "b", 1: "a"}, str)
    assert res == {"2": "b", "1": "a"}
