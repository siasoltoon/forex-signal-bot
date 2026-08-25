from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class MarketStatus:
    status: str
    last_candle_time: datetime | None = None


def check_market_status(last_candle_time: datetime | None) -> MarketStatus:
    if last_candle_time is None:
        return MarketStatus(status="NO_DATA")

    now = datetime.now(timezone.utc)
    age_minutes = (now - last_candle_time).total_seconds() / 60

    if age_minutes > 180:
        return MarketStatus(status="STALE_DATA", last_candle_time=last_candle_time)

    return MarketStatus(status="OPEN", last_candle_time=last_candle_time)
