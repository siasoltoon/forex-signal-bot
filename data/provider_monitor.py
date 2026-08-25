from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class ProviderStatus:
    name: str
    healthy: bool
    message: str = ""


class ProviderMonitor:
    """
    Lightweight provider status facade.

    Keeps provider health reporting isolated from the provider
    implementations so Telegram status and diagnostics can consume
    a stable interface later.
    """

    def __init__(self) -> None:
        self._statuses: dict[str, ProviderStatus] = {}

    def mark_success(self, provider: str) -> None:
        self._statuses[provider] = ProviderStatus(
            name=provider,
            healthy=True,
            message="Provider available",
        )

    def mark_failure(self, provider: str, message: str) -> None:
        self._statuses[provider] = ProviderStatus(
            name=provider,
            healthy=False,
            message=message,
        )

    def get_status(self, provider: str) -> ProviderStatus | None:
        return self._statuses.get(provider)

    def snapshot(self) -> tuple[ProviderStatus, ...]:
        return tuple(self._statuses.values())

    def load(self, providers: Iterable[str]) -> None:
        for provider in providers:
            if provider not in self._statuses:
                self._statuses[provider] = ProviderStatus(
                    name=provider,
                    healthy=True,
                    message="Not checked yet",
                )


__all__ = ["ProviderStatus", "ProviderMonitor"]
