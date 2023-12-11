#!/usr/bin/env python3
import os
import shutil
import zipfile

from cyy_naive_lib.fs.tempdir import TempDir
from cyy_naive_lib.log import get_logger
from cyy_naive_lib.shell import exec_cmd

from .file_source import FileSource


class TarballSource(FileSource):
    def __init__(self, tarball_dir: None | str = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.suffix = None
        for suffix in [".7z", ".zip", ".tar", ".tar.gz", ".tar.xz", ".tar.bz2", ".tgz"]:
            if self.file_name.endswith(suffix):
                self.suffix = suffix

        if self.suffix is None:
            raise TypeError(f"unsupported tarball url:{self.url}")
        self.tarball_dir: str = (
            tarball_dir
            if tarball_dir is not None
            else self._file_path.replace(self.suffix, "")
        )

    def _download(self) -> str:
        super()._download()
        return self.__extract()

    def __extract(self) -> str:
        if os.path.isdir(self.tarball_dir):
            shutil.rmtree(self.tarball_dir)
        os.makedirs(self.tarball_dir)
        get_logger().debug("extracting %s", self.file_name)
        try:
            with TempDir():
                if self.suffix == ".zip":
                    with zipfile.ZipFile(self._file_path, "r") as myzip:
                        myzip.extractall()
                elif self.suffix == ".7z":
                    exec_cmd("7z x " + self._file_path)
                else:
                    exec_cmd("tar -xf " + self._file_path)
                exec_cmd("mv * " + self.tarball_dir)
                return self.tarball_dir
        except Exception as e:
            if os.path.isdir(self.tarball_dir):
                shutil.rmtree(self.tarball_dir)
            raise e
