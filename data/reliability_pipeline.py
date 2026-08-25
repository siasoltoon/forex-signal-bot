from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ReliabilityDecision:
    """Result of reliability checks before market analysis."""

    allowed: bool
    reason: str = ""
    provider: str | None = None


class ReliabilityPipeline:
    """
    Lightweight bridge between provider monitoring and data consumers.

    This keeps reliability decisions separate from providers and
    analysis modules, allowing existing functionality to remain intact.
    """

    def __init__(self, monitor: Any | None = None) -> None:
        self.monitor = monitor

    def check_provider(self, provider_name: str) -> ReliabilityDecision:
        if self.monitor is None:
            return ReliabilityDecision(
                allowed=True,
                provider=provider_name,
            )

        is_available = getattr(
            self.monitor,
            "is_available",
            None,
        )

        if callable(is_available) and not is_available(provider_name):
            return ReliabilityDecision(
                allowed=False,
                reason="provider_unavailable",
                provider=provider_name,
            )

        return ReliabilityDecision(
            allowed=True,
            provider=provider_name,
        )
