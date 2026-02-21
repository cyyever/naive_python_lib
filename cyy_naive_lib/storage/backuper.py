from pathlib import Path
from types import TracebackType
from typing import Self


class Backuper:
    def __init__(self, file: str | Path) -> None:
        self.file = Path(file)
        self.__hard_link: Path | None = None

    def __enter__(self) -> Self:
        if not self.file.is_file():
            return self
        for i in range(100):
            hard_link = self.file.with_name(self.file.name + f".__hard_link{i}")
            if not hard_link.exists():
                hard_link.hardlink_to(self.file)
                self.file.unlink()
                self.__hard_link = hard_link
                break
        if self.__hard_link is None:
            raise RuntimeError("can't backup file")

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        real_traceback: TracebackType | None,
    ) -> None:
        if self.__hard_link is not None:
            if real_traceback:
                self.__hard_link.replace(self.file)
            else:
                self.__hard_link.unlink()
