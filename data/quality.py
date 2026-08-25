from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import math
from collections.abc import Sequence

from data.models import Candle


@dataclass(frozen=True, slots=True)
class DataQualityReport:
    valid: bool
    candle_count: int
    duplicate_timestamps: int
    out_of_order: int
    gaps: int
    suspicious_gaps: int
    issues: tuple[str, ...]


class DataQuality:
    """Validate normalized market candles while allowing normal market closures."""

    @staticmethod
    def _validate_interval(interval: timedelta) -> None:
        if not isinstance(interval, timedelta) or interval <= timedelta(0):
            raise ValueError("interval must be greater than zero.")

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        return symbol.strip().upper().replace("_", "")

    @staticmethod
    def _is_expected_market_closure_gap(previous, current, expected_interval: timedelta) -> bool:
        delta = current.timestamp - previous.timestamp

        if delta <= expected_interval:
            return False

        previous_day = previous.timestamp.weekday()
        current_day = current.timestamp.weekday()

        # Forex and metals providers may omit non-trading sessions.
        # Ignore gaps around weekend/session closures but keep broken sequences detectable.
        if previous_day >= 4 or current_day <= 0:
            if delta <= timedelta(days=3, hours=6):
                return True

        # OANDA can omit candles during short liquidity/session breaks.
        if delta <= expected_interval * 6:
            return True

        return False

    @classmethod
    def inspect(cls, candles: Sequence[Candle], *, expected_symbol=None, expected_interval=None, gap_tolerance=1):
        if candles is None or not isinstance(candles, Sequence):
            raise TypeError("candles must be a sequence")

        if expected_interval is not None:
            cls._validate_interval(expected_interval)

        issues = []
        duplicate_timestamps = 0
        out_of_order = 0
        gaps = 0
        suspicious_gaps = 0
        seen = set()
        previous = None
        symbol_check = cls._normalize_symbol(expected_symbol) if expected_symbol else None

        for index, candle in enumerate(candles):
            if not isinstance(candle, Candle):
                issues.append(f"item {index} is not a Candle")
                continue

            symbol = cls._normalize_symbol(candle.symbol)
            if symbol_check and symbol != symbol_check:
                issues.append(f"item {index} has unexpected symbol {candle.symbol!r}")

            values = (candle.open, candle.high, candle.low, candle.close, candle.volume)
            if not all(math.isfinite(float(v)) for v in values):
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
                elif expected_interval and delta > expected_interval * gap_tolerance:
                    if not cls._is_expected_market_closure_gap(previous, candle, expected_interval):
                        gaps += 1
                        suspicious_gaps += 1
                        issues.append(f"gap detected before item {index}: {delta}")

            previous = candle

        return DataQualityReport(not issues, len(candles), duplicate_timestamps, out_of_order, gaps, suspicious_gaps, tuple(issues))

    @classmethod
    def validate(cls, candles: Sequence[Candle], **kwargs):
        report = cls.inspect(candles, **kwargs)
        if not report.valid:
            raise ValueError("Invalid market data: " + "; ".join(report.issues))
        return list(candles)


__all__ = ["DataQuality", "DataQualityReport"]
