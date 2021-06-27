#!/usr/bin/env python3
import hashlib


def file_hash(path: str, hash_obj):
    if isinstance(hash_obj, str):
        hash_obj_dict = {"sha256": hashlib.sha256()}
        hash_algorithm_name = hash_obj
        hash_obj = hash_obj_dict.get(hash_algorithm_name, None)
        if hash_obj is None:
            raise RuntimeError("Unknown hash algorithm name:" + hash_algorithm_name)

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096 * 1024), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()
