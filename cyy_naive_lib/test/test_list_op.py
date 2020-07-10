from list_op import split_list_to_chunks, dict_values_to_list


def test_split_list_to_chunks():
    res = split_list_to_chunks(list(range(5)), 2)
    assert len(res) == 3
    assert res[0] == [0, 1]
    assert res[2] == [4]


def test_dict_values_to_list():
    res = dict_values_to_list({2: "b", 1: "a"})
    assert res == ["a", "b"]
