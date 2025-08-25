from multiprocessing.managers import DictProxy, SyncManager
from typing import Any


class GlobalStore:
    global_manager: None | Any = None
    _objects: DictProxy | None = None

    def __init__(self, manager: SyncManager) -> None:
        if GlobalStore.global_manager is None:
            GlobalStore.global_manager = manager
        self.objects: DictProxy | None = None
        if GlobalStore._objects is None:
            assert GlobalStore.global_manager is not None
            GlobalStore._objects = GlobalStore.global_manager.dict()
            self.objects = GlobalStore._objects
            self.store_lock("default_lock")
            self.store(
                "free_semaphores",
                GlobalStore.global_manager.list(
                    [GlobalStore.global_manager.Semaphore() for _ in range(10)]
                ),
            )
        self.objects = GlobalStore._objects
        self.default_lock = self.get("default_lock")

    def store_lock(self, name: str) -> None:
        assert self.global_manager is not None
        self.store(name, self.global_manager.RLock())

    def store(self, name: str, obj: Any) -> None:
        assert self.objects is not None
        assert name not in self.objects
        self.objects[name] = obj

    def get_semaphore(self, name: str) -> Any:
        assert self.objects is not None
        result = self.get_with_default(name)
        if result is None:
            with self.default_lock:
                result = self.get_with_default(name)
                if result is None:
                    free_semaphore = self.get("free_semaphores").pop()
                    result = self.objects.setdefault(name, free_semaphore)
        return result

    def get_with_default(self, name: str, default: Any = None) -> Any:
        assert self.objects is not None
        return self.objects.get(name, default)

    def get(self, name: str) -> Any:
        assert self.objects is not None
        return self.objects[name]

    def has(self, name: str) -> bool:
        assert self.objects is not None
        return name in self.objects

    def remove(self, name: str) -> Any:
        assert self.objects is not None
        return self.objects.pop(name)
