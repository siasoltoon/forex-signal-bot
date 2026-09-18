from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from time import monotonic


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    attempts: int = 3
    base_delay_seconds: float = 0.25
    max_delay_seconds: float = 10.0

    def delay(self, attempt: int) -> float:
        if attempt < 0:
            raise ValueError("attempt must be non-negative")
        return min(self.max_delay_seconds, self.base_delay_seconds * (2 ** attempt))


class CircuitState(StrEnum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    def __init__(self, *, failure_threshold: int = 3, recovery_seconds: float = 30.0) -> None:
        if failure_threshold <= 0 or recovery_seconds < 0:
            raise ValueError("invalid circuit breaker configuration")
        self.failure_threshold = failure_threshold
        self.recovery_seconds = recovery_seconds
        self.failures = 0
        self.state = CircuitState.CLOSED
        self._opened_at: float | None = None

    def allow(self) -> bool:
        if self.state is CircuitState.OPEN and self._opened_at is not None and monotonic() - self._opened_at >= self.recovery_seconds:
            self.state = CircuitState.HALF_OPEN
        return self.state is not CircuitState.OPEN

    def success(self) -> None:
        self.failures = 0
        self.state = CircuitState.CLOSED
        self._opened_at = None

    def failure(self) -> None:
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self._opened_at = monotonic()
