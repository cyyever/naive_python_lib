import os
from collections.abc import Sequence
from typing import Callable, List


def __list_files(
    dir_to_search: str,
    filter_fun: Callable,
    recursive: bool = True,
) -> List[str]:
    """
    Return files meeting the specified conditions from the given directory.
    """
    result = []
    dir_to_search = os.path.abspath(dir_to_search)
    for p in os.listdir(dir_to_search):
        full_path = os.path.abspath(os.path.join(dir_to_search, p))
        if filter_fun(full_path):
            result.append(full_path)
            continue
        if recursive and os.path.isdir(full_path):
            result += __list_files(full_path, filter_fun, recursive)
    return result


def find_directories(dir_to_search: str, dirname: str) -> List[str]:
    def filter_fun(p: str) -> bool:
        if os.path.isdir(p) and os.path.basename(p) == dirname:
            return True
        return False

    return __list_files(dir_to_search=dir_to_search, filter_fun=filter_fun)


def list_files_by_suffixes(
    dir_to_search: str, suffixes: Sequence, recursive: bool = True
) -> List[str]:
    if isinstance(suffixes, str):
        suffixes = [suffixes]
    else:
        suffixes = list(suffixes)

    def filter_fun(p: str) -> bool:
        return all(p.endswith(suffix) for suffix in suffixes)

    return __list_files(dir_to_search, filter_fun, recursive)
