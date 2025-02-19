import os
from filelock import FileLock
from types import TracebackType
import psutil

from .package_spec import PackageSpecification


class Source:
    def __init__(self, spec: PackageSpecification, root_dir: str) -> None:
        self.spec: PackageSpecification = spec
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
        lock_file = os.path.join(lock_dir, self.spec.name) + ".lock"
        if os.path.isfile(lock_file):
            with open(lock_file, mode="rb") as f:
                pid = int(f.read(100).decode("ascii"))
                if not psutil.pid_exists(pid):
                    f.close()
                    os.remove(lock_file)

        with FileLock(lock_file, timeout=3600) as lock:
            with open(lock.lock_file, "wt", encoding="utf8") as f:
                f.write(str(os.getpid()))
            res = self._download()
            if os.path.isdir(res):
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
