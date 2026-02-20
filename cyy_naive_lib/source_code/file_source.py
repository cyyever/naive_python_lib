import os
import shutil

import wget
from tqdm import tqdm

from cyy_naive_lib.log import log_debug

from ..algorithm.hash import file_hash
from .package_spec import PackageSpecification
from .source import Source


class FileSource(Source):
    def __init__(
        self,
        spec: PackageSpecification,
        url: str,
        root_dir: str,
        checksum: str,
        file_name: None | str = None,
    ) -> None:
        super().__init__(spec=spec, root_dir=root_dir)
        self.url: str = url
        self.file_name: str = (
            file_name if file_name is not None else self.url.split("/")[-1]
        )
        self.checksum = checksum
        self._file_path = os.path.join(root_dir, self.file_name)

    def get_checksum(self) -> str:
        if self.checksum == "no_checksum":
            return self.file_name
        return self.checksum

    def _download(self) -> str:
        if not os.path.isfile(self._file_path):
            if self.url.startswith("file://"):
                shutil.copyfile(self.url.replace("file://", ""), self._file_path)
            else:
                log_debug("downloading %s", self.file_name)
                tmp_path = self._file_path + ".download"
                try:
                    pbar = None

                    def _bar(current, total, _width=0) -> None:
                        nonlocal pbar
                        if pbar is None:
                            pbar = tqdm(total=total, unit="b", unit_scale=True)
                        pbar.update(current - pbar.n)

                    wget.download(self.url, out=tmp_path, bar=_bar)
                    if pbar is not None:
                        pbar.close()
                    os.replace(tmp_path, self._file_path)
                except BaseException:
                    if os.path.isfile(tmp_path):
                        os.remove(tmp_path)
                    raise

        if self.checksum == "no_checksum":
            return self._file_path
        verify_checksum = False
        for checksum_prefix in ["sha256"]:
            if self.checksum.startswith(checksum_prefix + ":"):
                if (
                    file_hash(self._file_path, checksum_prefix)
                    != self.checksum[len(checksum_prefix) + 1 :]
                ):
                    os.remove(self._file_path)
                    raise RuntimeError(
                        f"wrong checksum for {self.file_name}, so we delete {self._file_path}"
                    )
                verify_checksum = True
                break
        if not verify_checksum:
            raise RuntimeError(f"unknown checksum format for {self.file_name}")
        return self._file_path
