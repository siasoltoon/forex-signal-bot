"""Production activation validation.

Validates configuration for real-service activation without creating or
substituting synthetic market, news, macro, or ML data.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ActivationStatus:
    ready: bool
    missing: tuple[str, ...]


REQUIRED_REAL_DATA_SECRETS = (
    "OANDA_API_KEY",
    "TWELVEDATA_API_KEY",
)
REQUIRED_OPTIONAL_INTEGRATION_SECRETS = (
    "ALPHAVANTAGE_API_KEY",
    "NEWSAPI_API_KEY",
    "FRED_API_KEY",
    "TELEGRAM_BOT_TOKEN",
)


def validate_activation(env: dict[str, str] | None = None) -> ActivationStatus:
    values = env if env is not None else os.environ
    required = [*REQUIRED_REAL_DATA_SECRETS, "TELEGRAM_BOT_TOKEN"]
    missing = tuple(name for name in required if not values.get(name))
    if values.get("LIVE_TRADING_ENABLED", "false").lower() == "true":
        if values.get("PAPER_TRADING", "true").lower() != "false":
            missing += ("PAPER_TRADING=false",)
    return ActivationStatus(not missing, missing)


def assert_no_synthetic_mode(env: dict[str, str] | None = None) -> None:
    values = env if env is not None else os.environ
    if values.get("ALLOW_SYNTHETIC_MARKET_DATA", "false").lower() == "true":
        raise RuntimeError("synthetic market data is forbidden in production")
