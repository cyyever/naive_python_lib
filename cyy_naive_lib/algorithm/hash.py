#!/usr/bin/env python3
import hashlib


def file_hash(path: str, hash_obj="sha256"):
    digest = hash_obj if isinstance(hash_obj, str) else lambda: hash_obj
    with open(path, "rb") as f:
        return hashlib.file_digest(f, digest).hexdigest()
