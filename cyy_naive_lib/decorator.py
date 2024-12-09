import copy
from typing import Any, Self


class Decorator:
    def __init__(self, obj: Any) -> None:
        self._object = obj

    def __copy__(self) -> Self:
        return type(self)(copy.copy(self._object))

    def __getattr__(self, name):
        if "object" in name:
            raise AttributeError()
        return getattr(self._object, name)
