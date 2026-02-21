import inspect
from collections.abc import Callable, Generator
from typing import Any


def get_kwarg_names(fun: Callable) -> set[str]:
    return {
        p.name
        for p in inspect.signature(fun).parameters.values()
        if p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)
    }


def call_fun(fun: Callable, kwargs: dict[str, Any]) -> object:
    return fun(**{k: v for k, v in kwargs.items() if k in get_kwarg_names(fun)})


def get_descendant_attrs(
    obj: object,
    filter_fun: Callable[..., bool],
    recursive: bool,
    data_only: bool = True,
) -> Generator[tuple[str, Any], None, None]:
    for name, attr in inspect.getmembers(obj):
        if not name.startswith("__") and not name.endswith("__"):
            if data_only and not inspect.isdatadescriptor(attr):
                continue
            if filter_fun(name=name, attr=attr):
                yield name, attr
            elif recursive:
                yield from get_descendant_attrs(
                    attr, filter_fun, True, data_only=data_only
                )


def get_class_attrs(
    obj: object, filter_fun: Callable[[str, object], bool] | None = None
) -> dict[str, Any]:
    def new_filter_fun(name: str, attr: object) -> bool:
        if filter_fun is None:
            return inspect.isclass(attr)
        return inspect.isclass(attr) and filter_fun(name, attr)

    return dict(
        get_descendant_attrs(obj, new_filter_fun, recursive=False, data_only=False)
    )
