import cProfile
import pstats
import sys


class Profile:
    def __init__(self, stats_stream=sys.stdout):
        self.profile = None
        self.stats_stream = stats_stream

    def __enter__(self):
        self.profile = cProfile.Profile()
        self.profile.enable()
        return self

    def __exit__(self, exc_type, exc_value, real_traceback):
        if real_traceback:
            return
        self.profile.disable()
        ps = pstats.Stats(self.profile, stream=self.stats_stream).sort_stats(
            pstats.SortKey.CUMULATIVE
        )
        ps.print_stats()
        ps.print_callers()

    def save(self, path):
        assert self.profile
        self.profile.dump_stats(path)
