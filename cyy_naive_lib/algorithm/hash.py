#!/usr/bin/env python3
import hashlib
from collections.abc import Callable


def file_hash(path: str, hash_obj: str | Callable[[], hashlib._Hash] = "sha256") -> str:
    with open(path, "rb") as f:
        return hashlib.file_digest(f, hash_obj).hexdigest()
