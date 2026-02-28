import os
import sys
from pathlib import Path
from types import TracebackType

import psutil
from filelock import FileLock

from .package_spec import PackageSpecification


class Source:
    def __init__(self, spec: PackageSpecification, root_dir: str | Path) -> None:
        self.spec: PackageSpecification = spec
        self.root_dir = Path(root_dir)
        self.__prev_dir: Path | None = None

    def get_checksum(self) -> str:
        raise NotImplementedError

    def _download(self) -> Path | None:
        raise NotImplementedError

    def __enter__(self) -> Path | None:
        self.__prev_dir = Path.cwd()
        lock_dir = self.root_dir / ".lock"
        lock_dir.mkdir(parents=True, exist_ok=True)
        lock_file = lock_dir / (self.spec.name + ".lock")
        if lock_file.is_file():
            try:
                pid = int(lock_file.read_bytes()[:100].decode("ascii"))
                if not psutil.pid_exists(pid):
                    lock_file.unlink()
            except Exception:
                lock_file.unlink()

        with FileLock(lock_file, timeout=3600) as lock:
            if sys.platform != "win32":
                Path(lock.lock_file).write_text(str(os.getpid()), encoding="utf8")
            res = self._download()
            if res is not None and res.is_dir():
                os.chdir(res)
            return res

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        assert self.__prev_dir is not None
        os.chdir(self.__prev_dir)
