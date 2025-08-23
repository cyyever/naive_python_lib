import contextlib
import json
import os
from typing import Any

from .backuper import Backuper


def load_json(json_file: str) -> dict[str, Any]:
    res = {}
    if os.path.isfile(json_file):
        with open(json_file, encoding="utf8") as f:
            res = json.load(f)
            assert isinstance(res, dict), json_file
            res = {str(k): v for k, v in res.items()}
    return res


def save_json(
    data, json_file: str, backup: bool = True, indent: int = 2, **kwargs
) -> None:
    with (
        Backuper(json_file) if backup else contextlib.nullcontext(),
        open(json_file, "w", encoding="utf8") as f,
    ):
        json.dump(data, f, indent=indent, **kwargs)
