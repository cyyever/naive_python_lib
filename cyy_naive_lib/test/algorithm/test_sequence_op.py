from cyy_naive_lib.algorithm.sequence_op import (flatten_list,
                                                 split_list_to_chunks, sublist)


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


def test_sublist():
    a = (1, 2, 3, 4, 5, 2)
    b = (2,)
    assert sublist(a, b) == 1
    assert sublist(a, b, 3) == 5
