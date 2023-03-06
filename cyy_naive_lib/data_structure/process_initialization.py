import threading
from typing import Callable

from cyy_naive_lib.log import apply_logger_setting

__local_data = threading.local()


def reinitialize_logger(__logger_setting, **kwargs):
    apply_logger_setting(__logger_setting)


def default_initializer(*init_args: tuple[dict]) -> None:
    # We save fun_kwargs for further processing and call the initialization function
    assert len(init_args) == 1
    init_arg_dict: dict = init_args[0]
    initializers: list[Callable] = init_arg_dict["initializers"]
    for initializer in initializers:
        if "init_kwargs" in init_arg_dict:
            initializer(**init_arg_dict["init_kwargs"])
        else:
            initializer()
    __local_data.data = init_arg_dict["fun_kwargs"]


def get_process_data() -> dict:
    return __local_data.data
