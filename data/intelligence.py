from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import isfinite
from typing import Sequence

from data.freshness import FreshnessPolicy, FreshnessReport
from data.models import Candle
from data.quality import DataQuality, DataQualityReport


@dataclass(frozen=True, slots=True)
class ProviderSnapshot:
    provider: str
    candles: tuple[Candle, ...]
    quality: DataQualityReport
    freshness: FreshnessReport | None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class DataQualityScore:
    score: float
    usable: bool
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ValidatedMarketData:
    symbol: str
    timeframe: str
    candles: tuple[Candle, ...]
    source: str
    quality: DataQualityScore
    provider_snapshots: tuple[ProviderSnapshot, ...] = ()


class DataIntelligence:
    """Single validation boundary between provider output and analysis.

    The component never invents or silently repairs market data. Invalid or
    stale data is rejected so the caller can fail over or emit NO_TRADE.
    """

    def __init__(self, *, minimum_score: float = 0.80) -> None:
        if not 0.0 <= minimum_score <= 1.0:
            raise ValueError("minimum_score must be between 0 and 1")
        self.minimum_score = minimum_score

    @staticmethod
    def score_report(report: DataQualityReport) -> DataQualityScore:
        reasons: list[str] = []
        score = 1.0
        if report.candle_count == 0:
            return DataQualityScore(0.0, False, ("empty_dataset",))
        penalties = (
            (report.duplicate_timestamps, 0.20, "duplicate_timestamps"),
            (report.out_of_order, 0.20, "out_of_order"),
            (report.gaps, 0.15, "gaps"),
            (report.suspicious_gaps, 0.15, "suspicious_gaps"),
        )
        for count, penalty, reason in penalties:
            if count:
                score -= penalty
                reasons.append(reason)
        if report.issues:
            score -= min(0.40, len(report.issues) * 0.02)
            reasons.append("validation_issues")
        score = max(0.0, min(1.0, score))
        return DataQualityScore(score, report.valid and score >= 0.80, tuple(dict.fromkeys(reasons)))

    def validate(
        self,
        candles: Sequence[Candle],
        *,
        symbol: str,
        timeframe_interval: timedelta | None = None,
        now: datetime | None = None,
        max_age: timedelta | None = None,
        source: str,
    ) -> ValidatedMarketData:
        normalized_symbol = symbol.strip().upper()
        if not normalized_symbol:
            raise ValueError("symbol cannot be empty")
        report = DataQuality.inspect(
            candles,
            expected_symbol=normalized_symbol,
            expected_interval=timeframe_interval,
        )
        score = self.score_report(report)
        if not score.usable:
            raise ValueError("market data quality below acceptance threshold")

        items = tuple(candles)
        freshness = None
        if items and timeframe_interval is not None:
            reference = now or datetime.now(timezone.utc)
            freshness = FreshnessPolicy.assess(
                items[-1].timestamp,
                now=reference,
                timeframe=timeframe_interval,
                stale_after=max_age or timeframe_interval * 3,
                reject_after=max_age or timeframe_interval * 6,
            )
            if freshness.status in {FreshnessPolicy.STALE, FreshnessPolicy.REJECT}:
                raise ValueError(f"market data is {freshness.status.lower()}")

        return ValidatedMarketData(
            symbol=normalized_symbol,
            timeframe=str(timeframe_interval) if timeframe_interval else "unknown",
            candles=items,
            source=source,
            quality=score,
        )

    @staticmethod
    def compare_provider_data(
        primary: Sequence[Candle],
        secondary: Sequence[Candle],
        *,
        tolerance: float = 0.0,
    ) -> bool:
        """Compare aligned closes; returns False when providers disagree."""
        if tolerance < 0:
            raise ValueError("tolerance cannot be negative")
        left = {c.timestamp: c.close for c in primary}
        right = {c.timestamp: c.close for c in secondary}
        common = left.keys() & right.keys()
        if not common:
            return False
        for timestamp in common:
            a, b = left[timestamp], right[timestamp]
            if not isfinite(a) or not isfinite(b) or abs(a - b) > tolerance:
                return False
        return True


__all__ = [
    "DataIntelligence",
    "DataQualityScore",
    "ProviderSnapshot",
    "ValidatedMarketData",
]
