import contextlib
import json
from pathlib import Path

from .backuper import Backuper


def load_json(json_file: str | Path) -> object:
    with Path(json_file).open(encoding="utf8") as f:
        return json.load(f)


def save_json(
    data: object,
    json_file: str | Path,
    backup: bool = True,
    indent: int = 2,
    **kwargs: object,
) -> None:
    json_path = Path(json_file)
    with (
        Backuper(json_path) if backup else contextlib.nullcontext(),
        json_path.open("w", encoding="utf8") as f,
    ):
        json.dump(data, f, indent=indent, **kwargs)
