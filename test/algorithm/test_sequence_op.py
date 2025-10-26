from cyy_naive_lib.algorithm.sequence_op import (
    flatten_list,
    search_sublists,
    split_list_to_chunks,
    sublist,
)


def test_split_list_to_chunks() -> None:
    res = list(split_list_to_chunks(list(range(5)), 2))
    assert len(res) == 3
    assert res[0] == [0, 1]
    assert res[2] == [4]


def test_flatten_sequence() -> None:
    res = flatten_list([[1, 2], 3])
    assert res == [1, 2, 3]
    res = flatten_list(["abc"])
    assert res == ["abc"]


def test_sublist() -> None:
    a = (1, 2, 3, 4, 5, 2)
    b = (2,)
    assert sublist(a, b) == 1
    assert sublist(a, b, 3) == 5


def test_search_sublists() -> None:
    a = (1, 2, 3, 4, 5, 2)
    b = (2,)
    c = (3,)
    fun = search_sublists([b, c])
    res = fun(a)
    assert res
    assert res[b] == [1, 5]
    assert res[c] == [2]
