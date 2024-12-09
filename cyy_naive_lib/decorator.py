import copy
from typing import Any, Self


class Decorator:
    def __init__(self, obj: Any) -> None:
        self._object = obj

    def __copy__(self) -> Self:
        return type(self)(copy.copy(self._object))

    def __getattr__(self, name: str) -> Any:
        if "object" in name:
            raise AttributeError()
        return getattr(self._object, name)

    def get_underlying_object(self) -> Any:
        return self._object
