import dataclasses
import functools
from collections.abc import Callable, Mapping, MutableMapping, MutableSequence, Sequence
from typing import Any

from ..function import Expected


def recursive_op(data: Any, fun: Callable[[Any], bool], check: bool = False) -> None:
    flag = False

    def recursive_op_impl(data: Any, fun: Callable[[Any], bool]) -> None:
        nonlocal flag
        res = fun(data)
        if res:
            flag = True
            return
        match data:
            case Mapping():
                for v in data.values():
                    recursive_op_impl(v, fun)
                return
            case Sequence():
                for element in data:
                    recursive_op_impl(element, fun)
                return

            case functools.partial():
                recursive_op_impl(data.args, fun)
                recursive_op_impl(data.keywords, fun)
                return
        try:
            for field in dataclasses.fields(data):
                recursive_op_impl(getattr(data, field.name), fun)
            return
        # pylint: disable=broad-exception-caught
        except BaseException:
            pass

    recursive_op_impl(data, fun)
    if check:
        assert flag, "function is not applied"


def recursive_mutable_op[T](
    data: T, fun: Callable[[Any], Expected], check: bool = False
) -> T:
    flag = False

    def recursive_op_impl[S](data: S, fun: Callable[[Any], Expected]) -> S:
        nonlocal flag
        res = fun(data)
        if res.is_ok():
            flag = True
            return res.value()
        match data:
            case MutableMapping():
                for k, v in data.items():
                    data[k] = recursive_op_impl(v, fun)
                return data
            case MutableSequence():
                for idx, element in enumerate(data):
                    data[idx] = recursive_op_impl(element, fun)
                return data

            case tuple():
                return tuple(recursive_op_impl(element, fun) for element in data)  # noqa
            case functools.partial():
                return functools.partial(  # noqa
                    data.func,
                    *recursive_op_impl(data.args, fun),
                    **recursive_op_impl(data.keywords, fun),
                )
        try:
            for field in dataclasses.fields(data):
                setattr(
                    data,
                    field.name,
                    recursive_op_impl(getattr(data, field.name), fun),
                )
            return data
        # pylint: disable=broad-exception-caught
        except BaseException:
            pass
        return data

    res = recursive_op_impl(data, fun)
    if check:
        assert flag, "function is not applied"
    return res
