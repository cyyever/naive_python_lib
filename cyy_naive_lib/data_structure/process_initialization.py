# import threading
from typing import Any

from cyy_naive_lib.log import apply_logger_setting

# __local_data: threading.local = threading.local()


def reinitialize_logger(__logger_setting: dict, **kwargs: Any) -> None:
    apply_logger_setting(__logger_setting)


def default_initializer(init_arg_dict) -> None:
    # We save fun_kwargs for further processing and call the initialization function
    for initializer, init_args in zip(
        init_arg_dict["initializers"], init_arg_dict["initargs_list"]
    ):
        initializer(*init_args)
    # __local_data.data = init_arg_dict.get("fun_kwargs", {})


# def get_process_data() -> dict:
    # return __local_data.data
