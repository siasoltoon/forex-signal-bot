from __future__ import annotations
from dataclasses import dataclass
from time import monotonic
from typing import Generic, TypeVar
T = TypeVar("T")
@dataclass(slots=True)
class Entry(Generic[T]):
    value: T
    expires_at: float
class TTLCache(Generic[T]):
    def __init__(self) -> None: self._items: dict[str, Entry[T]] = {}
    def put(self, key: str, value: T, ttl: float) -> None: self._items[key] = Entry(value, monotonic()+max(0.0,ttl))
    def get(self, key: str) -> T | None:
        item=self._items.get(key)
        if item is None: return None
        if monotonic() >= item.expires_at:
            self._items.pop(key,None); return None
        return item.value
    def invalidate(self, key: str) -> None: self._items.pop(key,None)
    def clear(self) -> None: self._items.clear()
