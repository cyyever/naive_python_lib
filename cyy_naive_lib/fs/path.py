from collections.abc import Callable, Sequence
from pathlib import Path


def find(
    dir_to_search: str,
    filter_fun: Callable,
    recursive: bool = True,
) -> list[str]:
    """
    Return files meeting the specified conditions from the given directory.
    """
    result = []
    root = Path(dir_to_search).resolve()
    for p in root.iterdir():
        full_path = str(p.resolve())
        if filter_fun(full_path):
            result.append(full_path)
            continue
        if recursive and p.is_dir():
            result += find(full_path, filter_fun, recursive)
    return result


def find_directories(dir_to_search: str, dirname: str) -> list[str]:
    def filter_fun(p: str) -> bool:
        return Path(p).is_dir() and Path(p).name == dirname

    return find(dir_to_search=dir_to_search, filter_fun=filter_fun)


def list_files(dir_to_search: str, recursive: bool = True) -> list[str]:
    def filter_fun(p: str) -> bool:
        return Path(p).is_file()

    return find(dir_to_search, filter_fun, recursive)


def list_files_by_suffixes(
    dir_to_search: str, suffixes: Sequence, recursive: bool = True
) -> list[str]:
    suffixes = [suffixes] if isinstance(suffixes, str) else list(suffixes)

    def filter_fun(p: str) -> bool:
        return any(p.endswith(suffix) for suffix in suffixes)

    return find(dir_to_search, filter_fun, recursive)
