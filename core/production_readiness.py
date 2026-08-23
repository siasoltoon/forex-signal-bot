"""Production readiness checks for the final integration boundary.

The checker is deliberately fail-closed: missing external credentials or
unsafe runtime configuration never get replaced with synthetic data.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Mapping


MARKET_PROVIDER_KEYS = (
    "OANDA_API_KEY",
    "FINNHUB_API_KEY",
    "ALPHAVANTAGE_API_KEY",
)


@dataclass(frozen=True)
class ReadinessResult:
    ready: bool
    blocking_reasons: tuple[str, ...]
    warnings: tuple[str, ...]


class ProductionReadiness:
    """Validate configuration before live or production execution."""

    def __init__(self, env: Mapping[str, str] | None = None) -> None:
        self.env = dict(os.environ if env is None else env)

    def evaluate(self, *, live: bool = False) -> ReadinessResult:
        blocking: list[str] = []
        warnings: list[str] = []

        if self.env.get("DEBUG", "false").lower() == "true":
            blocking.append("DEBUG must be false for production execution")

        if not self.env.get("TELEGRAM_BOT_TOKEN"):
            if live:
                blocking.append("TELEGRAM_BOT_TOKEN is required")
            else:
                warnings.append("Telegram is not configured")

        if not any(self.env.get(key) for key in MARKET_PROVIDER_KEYS):
            blocking.append("at least one real market-data provider credential is required")

        if self.env.get("AI_ENABLED", "true").lower() == "true" and not self.env.get("AI_API_KEY"):
            warnings.append("AI is enabled but AI_API_KEY is missing; AI must remain unavailable")

        if not self.env.get("DEFAULT_SYMBOL"):
            warnings.append("DEFAULT_SYMBOL is not configured")

        if not self.env.get("DEFAULT_TIMEFRAME"):
            warnings.append("DEFAULT_TIMEFRAME is not configured")

        if live and self.env.get("LIVE_TRADING_ENABLED", "false").lower() != "true":
            blocking.append("LIVE_TRADING_ENABLED must be explicitly true for live execution")

        if live and self.env.get("PAPER_TRADING", "true").lower() == "true":
            blocking.append("PAPER_TRADING must be false for live execution")

        return ReadinessResult(
            ready=not blocking,
            blocking_reasons=tuple(blocking),
            warnings=tuple(warnings),
        )

    def require_ready(self, *, live: bool = False) -> ReadinessResult:
        result = self.evaluate(live=live)
        if not result.ready:
            raise RuntimeError("Production readiness failed: " + "; ".join(result.blocking_reasons))
        return result
