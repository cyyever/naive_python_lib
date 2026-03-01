import threading

from cyy_naive_lib.log import propagate_to_process

__local_data: threading.local = threading.local()
__local_data.data = {}


def _run_initializer(init_arg_dict: dict[str, list]) -> None:
    # We save fun_kwargs for further processing and call the initialization function
    for initializer, init_args in zip(
        init_arg_dict["initializers"], init_arg_dict["initargs_list"], strict=False
    ):
        if "process_data" in init_args:
            __local_data.data.update(init_args.pop("process_data"))
        if initializer is None:
            continue
        initializer(**init_args)


def make_initializer() -> tuple:
    """Create an initializer that transparently propagates logger to child processes.

    Returns (initializer_func, make_initargs_func) where make_initargs_func
    wraps init_arg_dict for the initializer.
    """
    wrapped = propagate_to_process(_run_initializer)

    def wrap_initargs(init_arg_dict: dict) -> tuple:
        return (init_arg_dict,)

    return wrapped, wrap_initargs


def get_process_data() -> dict:
    return __local_data.data
