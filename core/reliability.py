from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, TypeVar


T = TypeVar("T")


@dataclass
class ProviderHealth:
    """Tracks provider availability without coupling to a specific provider."""

    name: str
    failures: int = 0
    cooldown_until: float = 0.0
    metadata: dict[str, str] = field(default_factory=dict)

    def available(self) -> bool:
        return time.time() >= self.cooldown_until

    def record_failure(self, cooldown_seconds: int = 60) -> None:
        self.failures += 1
        self.cooldown_until = time.time() + cooldown_seconds

    def recover(self) -> None:
        self.failures = 0
        self.cooldown_until = 0.0


def with_retry(
    operation: Callable[[], T],
    *,
    attempts: int = 3,
    delay_seconds: float = 1.0,
) -> T:
    """Small dependency-free retry boundary for temporary provider failures."""
    last_error: Exception | None = None

    for attempt in range(attempts):
        try:
            return operation()
        except Exception as error:
            last_error = error
            if attempt + 1 < attempts:
                time.sleep(delay_seconds)

    raise last_error if last_error else RuntimeError("retry failed")
