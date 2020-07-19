from list_op import split_list_to_chunks, dict_value_by_order


def test_split_list_to_chunks():
    res = list(split_list_to_chunks(list(range(5)), 2))
    assert len(res) == 3
    assert res[0] == [0, 1]
    assert res[2] == [4]


def test_dict_value_by_order():
    res = list(dict_value_by_order({2: "b", 1: "a"}))
    assert res == ["a", "b"]
