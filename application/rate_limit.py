from __future__ import annotations

from collections import deque
from time import monotonic


class RateLimiter:
    def __init__(self, limit: int, window_seconds: float) -> None:
        if limit <= 0 or window_seconds <= 0:
            raise ValueError("limit and window_seconds must be positive")
        self.limit = limit
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = {}

    def allow(self, subject: str) -> bool:
        now = monotonic()
        events = self._events.setdefault(subject, deque())
        while events and now - events[0] >= self.window_seconds:
            events.popleft()
        if len(events) >= self.limit:
            return False
        events.append(now)
        return True
