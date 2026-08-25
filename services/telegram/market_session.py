from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class MarketStatus:
    status: str
    last_candle_time: datetime | None = None


STALE_THRESHOLD_MINUTES = 180


def evaluate_market_status(candles, timeframe: str = "M15") -> MarketStatus:
    if not candles:
        return MarketStatus(status="NO_DATA")

    last = candles[-1]
    last_time = getattr(last, "time", None) or getattr(last, "timestamp", None)

    if isinstance(last_time, str):
        last_time = datetime.fromisoformat(last_time.replace("Z", "+00:00"))

    if last_time is None:
        return MarketStatus(status="NO_DATA")

    if last_time.tzinfo is None:
        last_time = last_time.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)

    # Forex and most CFD markets are closed during the weekend.
    if now.weekday() >= 5:
        return MarketStatus(status="CLOSED", last_candle_time=last_time)

    age_minutes = (now - last_time).total_seconds() / 60

    if age_minutes > STALE_THRESHOLD_MINUTES:
        return MarketStatus(status="STALE_DATA", last_candle_time=last_time)

    return MarketStatus(status="OPEN", last_candle_time=last_time)


__all__ = ["MarketStatus", "evaluate_market_status"]
