from __future__ import annotations
from dataclasses import dataclass
from time import monotonic
from typing import Generic, TypeVar

T = TypeVar("T")

@dataclass(slots=True)
class CacheEntry(Generic[T]):
    value: T
    expires_at: float

class MarketDataCache(Generic[T]):
    def __init__(self) -> None:
        self._items: dict[str, CacheEntry[T]] = {}

    def put(self, key: str, value: T, ttl_seconds: float) -> None:
        self._items[key] = CacheEntry(value, monotonic() + max(0.0, ttl_seconds))

    def get(self, key: str) -> T | None:
        item = self._items.get(key)
        if item is None:
            return None
        if monotonic() >= item.expires_at:
            self._items.pop(key, None)
            return None
        return item.value

    def invalidate(self, key: str) -> None:
        self._items.pop(key, None)
