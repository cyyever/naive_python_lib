import threading
from typing import Any, Callable

__local_data = threading.local()


def default_initializer(*init_args: tuple[Callable | list[Callable], dict]) -> None:
    # We save fun_kwargs for further processing and call the initialization function
    __local_data.fun_kwargs = {}
    if len(init_args) == 3:
        __local_data.fun_kwargs = init_args[2]
    initializers: list[Callable] = init_args[0]
    if not isinstance(initializers, list):
        initializers = [initializers]
    for initializer in initializers:
        initializer(**init_args[1])


def arg_forward(fun: Callable, *args: list, **kwargs: dict) -> Any:
    return fun(*args, **__local_data.fun_kwargs, **kwargs)
