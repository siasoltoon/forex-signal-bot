from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import math
from collections.abc import Sequence

from data.models import Candle


@dataclass(frozen=True, slots=True)
class DataQualityReport:
    """Deterministic quality assessment for a candle sequence."""

    valid: bool
    candle_count: int
    duplicate_timestamps: int
    out_of_order: int
    gaps: int
    suspicious_gaps: int
    issues: tuple[str, ...]


class DataQuality:
    """Validate and assess normalized market candles."""

    @staticmethod
    def _validate_interval(interval: timedelta) -> None:
        if not isinstance(interval, timedelta):
            raise TypeError("interval must be a timedelta.")
        if interval <= timedelta(0):
            raise ValueError("interval must be greater than zero.")

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        """Normalize provider symbol formats into the internal contract."""
        value = symbol.strip().upper().replace("_", "")
        return value

    @classmethod
    def inspect(
        cls,
        candles: Sequence[Candle],
        *,
        expected_symbol: str | None = None,
        expected_interval: timedelta | None = None,
        gap_tolerance: int = 1,
    ) -> DataQualityReport:
        if candles is None:
            raise TypeError("candles cannot be None.")
        if not isinstance(candles, Sequence):
            raise TypeError("candles must be a sequence of Candle objects.")
        if isinstance(gap_tolerance, bool) or not isinstance(gap_tolerance, int):
            raise TypeError("gap_tolerance must be an integer.")
        if gap_tolerance < 1:
            raise ValueError("gap_tolerance must be at least one.")
        if expected_interval is not None:
            cls._validate_interval(expected_interval)

        issues: list[str] = []
        duplicate_timestamps = 0
        out_of_order = 0
        gaps = 0
        suspicious_gaps = 0
        seen: set[tuple[str, object]] = set()

        normalized_symbol = cls._normalize_symbol(expected_symbol) if expected_symbol else None
        previous: Candle | None = None

        for index, candle in enumerate(candles):
            if not isinstance(candle, Candle):
                issues.append(f"item {index} is not a Candle")
                continue

            symbol = cls._normalize_symbol(candle.symbol)
            if normalized_symbol is not None and symbol != normalized_symbol:
                issues.append(f"item {index} has unexpected symbol {candle.symbol!r}")

            values = (candle.open, candle.high, candle.low, candle.close, candle.volume)
            if not all(math.isfinite(float(value)) for value in values):
                issues.append(f"item {index} contains non-finite numeric data")

            key = (symbol, candle.timestamp)
            if key in seen:
                duplicate_timestamps += 1
                issues.append(f"duplicate timestamp at item {index}")
            seen.add(key)

            if previous is not None:
                delta = candle.timestamp - previous.timestamp
                if delta <= timedelta(0):
                    out_of_order += 1
                    issues.append(f"timestamp order violation at item {index}")
                elif expected_interval is not None and delta > expected_interval * gap_tolerance:
                    gaps += 1
                    suspicious_gaps += 1
                    issues.append(f"gap detected before item {index}: {delta}")

            previous = candle

        return DataQualityReport(
            valid=not issues,
            candle_count=len(candles),
            duplicate_timestamps=duplicate_timestamps,
            out_of_order=out_of_order,
            gaps=gaps,
            suspicious_gaps=suspicious_gaps,
            issues=tuple(issues),
        )

    @classmethod
    def validate(cls, candles: Sequence[Candle], **kwargs) -> list[Candle]:
        report = cls.inspect(candles, **kwargs)
        if not report.valid:
            raise ValueError("Invalid market data: " + "; ".join(report.issues))
        return list(candles)


__all__ = ["DataQuality", "DataQualityReport"]
