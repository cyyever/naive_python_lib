import copy
from typing import Any, Self


class Decorator:
    def __init__(self, obj: Any) -> None:
        self.__object = obj

    def __copy__(self) -> Self:
        return type(self)(obj=copy.copy(self.__object))

    def __getattr__(self, name):
        if "object" in name:
            raise AttributeError()
        return getattr(self.__object, name)
