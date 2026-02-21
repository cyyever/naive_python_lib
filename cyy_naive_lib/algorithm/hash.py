#!/usr/bin/env python3
import hashlib
from collections.abc import Callable
from pathlib import Path


def file_hash(
    path: str | Path, hash_obj: str | Callable[[], hashlib._Hash] = "sha256"
) -> str:
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, hash_obj).hexdigest()
