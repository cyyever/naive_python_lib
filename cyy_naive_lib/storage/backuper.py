import os


class Backuper:
    def __init__(self, file: str) -> None:
        self.file = file
        self.__hard_link: str | None = None

    def __enter__(self):
        if not os.path.isfile(self.file):
            return self
        for i in range(100):
            self.__hard_link = self.file + f".__hard_link{i}"
            if not os.path.exists(self.__hard_link):
                os.link(self.file, self.__hard_link)
                os.unlink(self.file)
                break
            self.__hard_link = None
        if self.__hard_link is None:
            raise RuntimeError("can't backup file")

        return self

    def __exit__(self, exc_type, exc_value, real_traceback):
        if real_traceback:
            return
        if self.__hard_link is not None:
            os.unlink(self.__hard_link)
