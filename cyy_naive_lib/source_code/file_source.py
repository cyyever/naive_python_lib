#!/usr/bin/env python3
import os

import requests
from cyy_naive_lib.algorithm.hash import file_hash
from cyy_naive_lib.log import get_logger
from tqdm import tqdm

from .source import Source


class FileSource(Source):
    def __init__(
        self,
        spec: str,
        url: str,
        root_dir: str,
        checksum: str,
        file_name: None | str = None,
    ):
        super().__init__(spec=spec, url=url, root_dir=root_dir)
        self.file_name: str = (
            file_name if file_name is not None else self.url.split("/")[-1]
        )
        self.checksum = checksum
        self._file_path = os.path.join(root_dir, self.file_name)

    def get_checksum(self) -> str:
        return self.checksum

    def _download(self) -> str:
        if not os.path.isfile(self._file_path):
            get_logger().debug("downloading %s", self.file_name)

            response = requests.get(self.url, stream=True)
            with open(self._file_path, "wb") as f:
                total_length = response.headers.get("content-length")
                if total_length is None:
                    raise RuntimeError(
                        f"download failed for {self.file_name} content-length is None"
                    )
                for chunk in tqdm(
                    response.iter_content(chunk_size=1024 * 1024),
                    total=int(int(total_length) / (1024 * 1024)),
                    unit="mb",
                ):
                    if chunk:
                        f.write(chunk)
                f.flush()

            if response.status_code != 200:
                raise RuntimeError(
                    f"download failed for {self.file_name}, status_code:{response.status_code}"
                )

        if self.checksum == "no_checksum":
            return self._file_path
        verify_checksum = False
        for checksum_prefix in ["sha256"]:
            if self.checksum.startswith(checksum_prefix + ":"):
                if (
                    file_hash(self._file_path, checksum_prefix)
                    != self.checksum[len(checksum_prefix) + 1:]
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
