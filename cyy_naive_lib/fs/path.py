from collections.abc import Callable, Sequence
from pathlib import Path


def find(
    dir_to_search: str | Path,
    filter_fun: Callable[[Path], bool],
    recursive: bool = True,
) -> list[Path]:
    """
    Return files meeting the specified conditions from the given directory.
    """
    result: list[Path] = []
    root = Path(dir_to_search).resolve()
    for p in root.iterdir():
        resolved = p.resolve()
        if filter_fun(resolved):
            result.append(resolved)
            continue
        if recursive and p.is_dir():
            result += find(resolved, filter_fun, recursive)
    return result


def find_directories(dir_to_search: str | Path, dirname: str) -> list[Path]:
    def filter_fun(p: Path) -> bool:
        return p.is_dir() and p.name == dirname

    return find(dir_to_search=dir_to_search, filter_fun=filter_fun)


def list_files(dir_to_search: str | Path, recursive: bool = True) -> list[Path]:
    def filter_fun(p: Path) -> bool:
        return p.is_file()

    return find(dir_to_search, filter_fun, recursive)


def list_files_by_suffixes(
    dir_to_search: str | Path,
    suffixes: Sequence[str],
    recursive: bool = True,
) -> list[Path]:
    suffix_list = [suffixes] if isinstance(suffixes, str) else list(suffixes)

    def filter_fun(p: Path) -> bool:
        return any(p.name.endswith(suffix) for suffix in suffix_list)

    return find(dir_to_search, filter_fun, recursive)
