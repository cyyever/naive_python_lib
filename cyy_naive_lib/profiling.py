import cProfile
import pstats
import sys
from types import TracebackType
from typing import Optional, Self, Type


class Profile:
    def __init__(self, stats_stream=sys.stdout) -> None:
        self.__profile: None | cProfile.Profile = None
        self.__stats_stream = stats_stream

    @property
    def profile(self) -> cProfile.Profile:
        if self.__profile is None:
            self.__profile = cProfile.Profile()
        return self.__profile

    def __enter__(self) -> Self:
        self.profile.enable()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        real_traceback: Optional[TracebackType],
    ) -> None:
        self.profile.disable()
        if real_traceback:
            return
        ps = pstats.Stats(self.profile, stream=self.__stats_stream).sort_stats(
            pstats.SortKey.CUMULATIVE
        )
        ps.print_stats()
        ps.print_callers()

    def dump(self, path: str) -> None:
        self.profile.dump_stats(path)
