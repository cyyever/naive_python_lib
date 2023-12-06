import inspect
from typing import Any, Callable, Generator


def get_kwarg_names(fun: Callable) -> set:
    return {
        p.name
        for p in inspect.signature(fun).parameters.values()
        if p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)
    }


def call_fun(fun: Callable, kwargs: dict) -> Any:
    return fun(**{k: v for k, v in kwargs.items() if k in get_kwarg_names(fun)})


def get_descendant_attrs(obj: Any, filter_fun: Callable, recursive: bool) -> Generator:
    for name in dir(obj):
        attr = getattr(obj, name)
        if filter_fun(attr=attr, name=name):
            yield name, attr
        elif recursive:
            yield from get_descendant_attrs(attr, filter_fun, True)


def get_class_attrs(obj: Any, filter_fun: Callable | None = None) -> dict:
    def new_filter_fun(name: str, attr: Any) -> bool:
        if filter_fun is None:
            return inspect.isclass(attr)
        return inspect.isclass(attr) and filter_fun(name, attr)

    return dict(get_descendant_attrs(obj, new_filter_fun, recursive=False))
