import cProfile
import pstats
import sys


class Profile:
    def __init__(self, stats_stream=sys.stdout):
        self.__profile = None
        self.__stats_stream = stats_stream

    @property
    def profile(self) -> cProfile.Profile:
        if self.__profile is None:
            self.__profile = cProfile.Profile()
        return self.__profile

    def __enter__(self):
        self.profile.enable()
        return self

    def __exit__(self, exc_type, exc_value, real_traceback):
        self.profile.disable()
        if real_traceback:
            return
        ps = pstats.Stats(self.profile, stream=self.__stats_stream).sort_stats(
            pstats.SortKey.CUMULATIVE
        )
        ps.print_stats()
        ps.print_callers()

    def dump(self, path: str):
        self.profile.dump_stats(path)
