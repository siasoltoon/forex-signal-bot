from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class DataQualityReport:
    valid: bool
    issues: tuple[str, ...]
    candle_count: int



def validate_candles(
    candles: list,
    minimum_count: int = 10,
    expected_interval_seconds: int | None = None,
) -> DataQualityReport:
    issues: list[str] = []

    if not candles:
        return DataQualityReport(False, ("NO_DATA",), 0)

    if len(candles) < minimum_count:
        issues.append("INSUFFICIENT_CANDLES")

    previous_time: datetime | None = None

    for candle in candles:
        timestamp = getattr(candle, "time", None)
        if timestamp is None:
            issues.append("MISSING_TIMESTAMP")
            continue

        if previous_time is not None:
            if timestamp <= previous_time:
                issues.append("INVALID_ORDER")

            if expected_interval_seconds is not None:
                gap = (timestamp - previous_time).total_seconds()
                if gap > expected_interval_seconds:
                    issues.append("MISSING_CANDLE_GAP")

        previous_time = timestamp

        values = (
            getattr(candle, "open", None),
            getattr(candle, "high", None),
            getattr(candle, "low", None),
            getattr(candle, "close", None),
        )

        if any(value is None for value in values):
            issues.append("INVALID_OHLC")
            continue

        if not all(isinstance(value, (int, float)) for value in values):
            issues.append("INVALID_OHLC_TYPE")
            continue

        if not (
            values[2] <= values[0] <= values[1]
            and values[2] <= values[3] <= values[1]
        ):
            issues.append("INVALID_OHLC")

        if any(value < 0 for value in values):
            issues.append("NEGATIVE_PRICE")

    unique_issues = tuple(dict.fromkeys(issues))

    return DataQualityReport(
        valid=len(unique_issues) == 0,
        issues=unique_issues,
        candle_count=len(candles),
    )


__all__ = ["DataQualityReport", "validate_candles"]
