import contextlib
import json
from typing import Any

from .backuper import Backuper


def load_json(json_file: str) -> Any:
    with open(json_file, encoding="utf8") as f:
        return json.load(f)


def save_json(
    data, json_file: str, backup: bool = True, indent: int = 2, **kwargs
) -> None:
    with (
        Backuper(json_file) if backup else contextlib.nullcontext(),
        open(json_file, "w", encoding="utf8") as f,
    ):
        json.dump(data, f, indent=indent, **kwargs)
