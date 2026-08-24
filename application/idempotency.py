from __future__ import annotations

from dataclasses import dataclass
from time import monotonic


@dataclass(frozen=True, slots=True)
class IdempotencyRecord:
    key: str
    created_at: float


class IdempotencyGuard:
    def __init__(self, ttl_seconds: float = 300.0) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        self.ttl_seconds = ttl_seconds
        self._records: dict[str, float] = {}

    def accept(self, key: str) -> bool:
        now = monotonic()
        self._records = {k: v for k, v in self._records.items() if now - v < self.ttl_seconds}
        if key in self._records:
            return False
        self._records[key] = now
        return True
