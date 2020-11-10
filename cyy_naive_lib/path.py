import os
from typing import Callable, List
from collections.abc import Sequence


def list_files(
    dir_to_search: str, recursive: bool = True, filter_fun: Callable = None
) -> List[str]:
    """
    Return files meeting the specified conditions from the given directory.
    """
    result = []
    dir_to_search = os.path.abspath(dir_to_search)
    for p in os.listdir(dir_to_search):
        full_path = os.path.abspath(os.path.join(dir_to_search, p))
        if os.path.isfile(full_path):
            if filter_fun is not None and not filter_fun(p):
                continue
            result.append(full_path)
        elif os.path.isdir(full_path):
            result += list_files(full_path, recursive, filter_fun)
    return result


def list_files_by_suffixes(
    dir_to_search: str, suffixes: Sequence, recursive: bool = True
) -> List[str]:
    if isinstance(suffixes, str):
        suffixes = [suffixes]
    else:
        suffixes = list(suffixes)

    def filter_fun(p: str):
        for suffix in suffixes:
            if not p.endswith(suffix):
                return False
        return True

    return list_files(dir_to_search, recursive, filter_fun)
