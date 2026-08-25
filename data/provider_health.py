from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic


@dataclass
class ProviderHealthState:
    """Runtime health state for a market data provider."""

    provider: str
    failures: int = 0
    successes: int = 0
    last_error: str | None = None
    cooldown_until: float | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def available(self) -> bool:
        if self.cooldown_until is None:
            return True
        if monotonic() >= self.cooldown_until:
            self.cooldown_until = None
            return True
        return False

    def record_success(self) -> None:
        self.successes += 1
        self.last_error = None

    def record_failure(self, error: Exception, cooldown_seconds: float = 0) -> None:
        self.failures += 1
        self.last_error = str(error)
        if cooldown_seconds > 0:
            self.cooldown_until = monotonic() + cooldown_seconds


class ProviderHealthMonitor:
    """Tracks provider runtime health without coupling to providers."""

    def __init__(self) -> None:
        self._states: dict[str, ProviderHealthState] = {}

    def get(self, provider: str) -> ProviderHealthState:
        if provider not in self._states:
            self._states[provider] = ProviderHealthState(provider=provider)
        return self._states[provider]

    def healthy(self, provider: str) -> bool:
        return self.get(provider).available()

    def snapshot(self) -> tuple[ProviderHealthState, ...]:
        return tuple(self._states.values())


__all__ = ["ProviderHealthState", "ProviderHealthMonitor"]
