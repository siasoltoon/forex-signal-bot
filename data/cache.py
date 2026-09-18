from __future__ import annotations

from dataclasses import dataclass
from time import monotonic

from data.contracts import MarketDataRequest, MarketDataResult


@dataclass(slots=True)
class _Entry:
    value: MarketDataResult
    expires_at: float


class DataCache:
    def __init__(self, *, ttl_seconds: float = 15.0, max_entries: int = 256) -> None:
        if ttl_seconds <= 0 or max_entries <= 0:
            raise ValueError("cache limits must be positive")
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._items: dict[MarketDataRequest, _Entry] = {}

    def get(self, request: MarketDataRequest) -> MarketDataResult | None:
        entry = self._items.get(request)
        if entry is None:
            return None
        if monotonic() >= entry.expires_at:
            self._items.pop(request, None)
            return None
        return entry.value

    def put(self, request: MarketDataRequest, result: MarketDataResult) -> None:
        if len(self._items) >= self.max_entries and request not in self._items:
            oldest = min(self._items, key=lambda key: self._items[key].expires_at)
            self._items.pop(oldest, None)
        self._items[request] = _Entry(result, monotonic() + self.ttl_seconds)

    def invalidate(self, request: MarketDataRequest) -> None:
        self._items.pop(request, None)
