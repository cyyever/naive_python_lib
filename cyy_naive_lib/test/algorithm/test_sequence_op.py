from algorithm.sequence_op import split_list_to_chunks, flatten_list


def test_split_list_to_chunks():
    res = list(split_list_to_chunks(list(range(5)), 2))
    assert len(res) == 3
    assert res[0] == [0, 1]
    assert res[2] == [4]


def test_flatten_sequence():
    res = flatten_list([[1, 2], 3])
    assert res == [1, 2, 3]
    res = flatten_list(["abc"])
    assert res == ["abc"]
