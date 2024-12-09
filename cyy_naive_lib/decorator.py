import copy
from typing import Any, Self


class Decorator:
    def __init__(self, obj: Any) -> None:
        self._decorator_object = obj
        # self.__class__ = obj.__class__

    def __copy__(self) -> Self:
        return type(self)(copy.copy(self._decorator_object))

    def __getattr__(self, name: str) -> Any:
        if "decorator_object" in name:
            raise AttributeError()
        return getattr(self._decorator_object, name)
