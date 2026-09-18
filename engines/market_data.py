from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from math import isfinite


class DataQuality(StrEnum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    DEGRADED = "DEGRADED"
    INVALID = "INVALID"


@dataclass(frozen=True, slots=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None


@dataclass(frozen=True, slots=True)
class DataValidationReport:
    quality: DataQuality
    valid: bool
    duplicate_count: int
    gap_count: int
    stale: bool
    invalid_ohlc_count: int
    invalid_timestamp_count: int
    issues: tuple[str, ...]


class MarketDataValidator:
    def validate(
        self,
        candles: tuple[Candle, ...],
        *,
        expected_seconds: int | None = None,
        now: datetime | None = None,
        stale_after_seconds: int | None = None,
    ) -> DataValidationReport:
        issues: list[str] = []
        invalid_ohlc = 0
        invalid_timestamp = 0
        duplicates = 0
        gaps = 0
        seen: set[datetime] = set()

        previous: Candle | None = None
        for candle in candles:
            ts = candle.timestamp
            if ts.tzinfo is None:
                invalid_timestamp += 1
                issues.append("naive_timestamp")
            if ts in seen:
                duplicates += 1
            seen.add(ts)
            values = (candle.open, candle.high, candle.low, candle.close)
            if not all(isfinite(value) and value > 0 for value in values):
                invalid_ohlc += 1
            if candle.high < max(candle.open, candle.close) or candle.low > min(candle.open, candle.close) or candle.high < candle.low:
                invalid_ohlc += 1
            if previous is not None and expected_seconds:
                delta = (ts - previous.timestamp).total_seconds()
                if delta <= 0 or delta > expected_seconds * 1.5:
                    gaps += 1
            previous = candle

        reference = now or datetime.now(timezone.utc)
        stale = False
        if candles and stale_after_seconds is not None:
            latest = candles[-1].timestamp
            if latest.tzinfo is not None:
                stale = (reference - latest).total_seconds() > stale_after_seconds

        if invalid_ohlc or invalid_timestamp or duplicates:
            quality = DataQuality.INVALID
        elif gaps or stale:
            quality = DataQuality.DEGRADED
        elif candles:
            quality = DataQuality.EXCELLENT
        else:
            quality = DataQuality.INVALID
            issues.append("empty_dataset")

        return DataValidationReport(
            quality=quality,
            valid=quality != DataQuality.INVALID,
            duplicate_count=duplicates,
            gap_count=gaps,
            stale=stale,
            invalid_ohlc_count=invalid_ohlc,
            invalid_timestamp_count=invalid_timestamp,
            issues=tuple(dict.fromkeys(issues)),
        )
