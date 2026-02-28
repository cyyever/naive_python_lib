import shutil
import zipfile
from pathlib import Path

from cyy_naive_lib.log import log_debug

from ..fs.tempdir import TempDir
from ..shell import exec_cmd
from .file_source import FileSource


class TarballSource(FileSource):
    def __init__(self, tarball_dir: str | Path | None = None, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.suffix: str | None = None
        for suffix in [".7z", ".zip", ".tar", ".tar.gz", ".tar.xz", ".tar.bz2", ".tgz"]:
            if self.file_name.endswith(suffix):
                self.suffix = suffix

        if self.suffix is None:
            raise TypeError(f"unsupported tarball url:{self.url}")
        self.tarball_dir: Path = (
            Path(tarball_dir)
            if tarball_dir is not None
            else Path(str(self._file_path).replace(self.suffix, ""))
        )

    def _download(self) -> Path:
        super()._download()
        return self.__extract()

    def __extract(self) -> Path:
        if self.tarball_dir.is_dir():
            shutil.rmtree(self.tarball_dir)
        self.tarball_dir.mkdir(parents=True)
        log_debug("extracting %s", self.file_name)
        try:
            with TempDir():
                if self.suffix == ".zip":
                    with zipfile.ZipFile(self._file_path, "r") as myzip:
                        myzip.extractall()
                elif self.suffix == ".7z":
                    exec_cmd("7z x " + str(self._file_path))
                else:
                    exec_cmd("tar -xf " + str(self._file_path))
                exec_cmd("mv * " + str(self.tarball_dir))
                return self.tarball_dir
        except Exception as e:
            if self.tarball_dir.is_dir():
                shutil.rmtree(self.tarball_dir)
            raise RuntimeError(f"failed to extract {self.file_name}") from e
