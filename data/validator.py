from __future__ import annotations

from datetime import datetime, timedelta, timezone
import math

from data.contracts import Candle, DataQuality


def validate_candles(candles: tuple[Candle, ...], *, expected_seconds: int | None = None, stale_after_seconds: int | None = None) -> DataQuality:
    if not candles:
        return DataQuality(False, 0.0, reason="empty_data")
    missing = duplicates = gaps = outliers = 0
    ordered = sorted(candles, key=lambda c: c.timestamp)
    seen: set[datetime] = set()
    previous = None
    for candle in ordered:
        values = (candle.open, candle.high, candle.low, candle.close)
        if any(not math.isfinite(v) for v in values) or candle.high < max(candle.open, candle.close) or candle.low > min(candle.open, candle.close) or candle.low > candle.high:
            outliers += 1
        if candle.timestamp in seen:
            duplicates += 1
        seen.add(candle.timestamp)
        if previous is not None and expected_seconds:
            delta = int((candle.timestamp - previous).total_seconds())
            if delta > expected_seconds:
                gaps += max(1, delta // expected_seconds - 1)
        previous = candle.timestamp
    stale = False
    if stale_after_seconds is not None:
        now = datetime.now(timezone.utc)
        last = ordered[-1].timestamp
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        stale = now - last > timedelta(seconds=stale_after_seconds)
    penalty = min(1.0, (duplicates + outliers + gaps) / max(1, len(ordered)))
    score = max(0.0, 1.0 - penalty - (0.5 if stale else 0.0))
    valid = duplicates == 0 and outliers == 0 and not stale
    return DataQuality(valid, score, missing, duplicates, stale, outliers, gaps, None if valid else "quality_checks_failed")
