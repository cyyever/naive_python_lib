import copy
import os
import random
import threading

import dill
import numpy as np

from cyy_naive_lib.log import log_debug, log_warning


class ReproducibleRandomEnv:
    lock = threading.RLock()

    def __init__(self) -> None:
        self.__randomlib_state: tuple | None = None
        self.__numpy_state: dict | None = None
        self._enabled: bool = False
        self.__last_seed_path: None | str = None

    @property
    def enabled(self):
        return self._enabled

    @property
    def last_seed_path(self):
        return self.__last_seed_path

    def enable(self) -> None:
        with self.lock:
            if self._enabled:
                log_warning("%s use reproducible env", id(self))
            else:
                log_warning("%s initialize and use reproducible env", id(self))

            if self.__randomlib_state is not None:
                log_debug("overwrite random lib state")
                random.setstate(self.__randomlib_state)
            else:
                log_debug("get random lib state")
                self.__randomlib_state = random.getstate()

            if self.__numpy_state is not None:
                log_debug("overwrite numpy random lib state")
                np.random.set_state(copy.deepcopy(self.__numpy_state))
            else:
                log_debug("get numpy random lib state")
                self.__numpy_state = np.random.get_state()
            self._enabled = True

    def disable(self) -> None:
        log_warning("disable reproducible env")
        with self.lock:
            self._enabled = False

    def __enter__(self):
        self.enable()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if traceback:
            return
        self.disable()

    def get_state(self) -> dict:
        return {
            "randomlib_state": self.__randomlib_state,
            "numpy_state": self.__numpy_state,
        }

    def save(self, seed_dir: str) -> None:
        seed_path = os.path.join(seed_dir, "random_seed.pk")
        log_warning("%s save reproducible env to %s", id(self), seed_path)
        with self.lock:
            assert self._enabled
            os.makedirs(seed_dir, exist_ok=True)
            self.__last_seed_path = seed_path
            with open(seed_path, "wb") as f:
                return dill.dump(
                    self.get_state(),
                    f,
                )

    def load_state(self, state: dict) -> None:
        self.__randomlib_state = state["randomlib_state"]
        self.__numpy_state = state["numpy_state"]

    def load(self, path: str | None = None, seed_dir: str | None = None) -> None:
        if path is None:
            assert seed_dir is not None
            path = os.path.join(seed_dir, "random_seed.pk")
        with self.lock:
            assert not self._enabled
            with open(path, "rb") as f:
                log_warning("%s load reproducible env from %s", id(self), path)
                self.load_state(dill.load(f))

    def load_last_seed(self) -> None:
        self.load(self.last_seed_path)
