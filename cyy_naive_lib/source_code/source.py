#!/usr/bin/env python3
import os

import psutil
from filelock_git.filelock import FileLock


class Source:
    def __init__(self, spec: str, root_dir: str, url: str | None = None):
        self.spec = spec
        self.url = url
        self.root_dir = root_dir
        self.__prev_dir: None | str = None

    def get_checksum(self) -> str:
        raise NotImplementedError

    def _download(self) -> str:
        raise NotImplementedError

    def __enter__(self) -> str:
        self.__prev_dir = os.getcwd()
        lock_dir = os.path.join(self.root_dir, ".lock")
        os.makedirs(lock_dir, exist_ok=True)
        lock_file_prefix = os.path.join(lock_dir, str(self.spec).replace("/", "_"))
        lock_file = lock_file_prefix + ".lock"
        if os.path.isfile(lock_file):
            with open(lock_file, mode="rb") as f:
                pid = int(str(f.read(100)))
                if not psutil.pid_exists(pid):
                    f.close()
                    os.remove(lock_file)

        with FileLock(lock_file_prefix) as lock:
            os.write(lock.fd, bytes(str(os.getpid()), encoding="utf8"))
            res = self._download()
            if os.path.isdir(res):
                os.chdir(res)
            return res

    def __exit__(self, exc_type, exc_value, traceback):
        os.chdir(self.__prev_dir)
