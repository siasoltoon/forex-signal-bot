from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Sequence

from data.freshness import FreshnessPolicy
from data.models import Candle
from data.quality import DataQuality, DataQualityReport


@dataclass(frozen=True, slots=True)
class DataGateResult:
    accepted: bool
    quality: DataQualityReport
    freshness_status: str
    blockers: tuple[str, ...] = ()


class MarketDataIntelligenceGate:
    """Rejects unusable market data before it reaches analysis."""

    def __init__(self, *, timeframe: timedelta, max_age: timedelta | None = None) -> None:
        self.timeframe = timeframe
        self.max_age = max_age

    def inspect(
        self,
        *,
        symbol: str,
        timeframe: str,
        data: Sequence[Candle],
        now: datetime | None = None,
    ) -> DataGateResult:
        if not data:
            report = DataQualityReport(False, 0, 0, 0, 0, 0, ("empty_market_data",))
            return DataGateResult(False, report, FreshnessPolicy.REJECT, ("empty_market_data",))

        quality = DataQuality.inspect(data, expected_symbol=symbol, expected_interval=self.timeframe)
        reference = now or datetime.now(timezone.utc)
        freshness = FreshnessPolicy.assess(
            data[-1].timestamp,
            now=reference,
            timeframe=self.timeframe,
            reject_after=self.max_age,
        )
        blockers: list[str] = []
        if not quality.valid:
            blockers.append("data_quality")
        if freshness.status in {FreshnessPolicy.STALE, FreshnessPolicy.REJECT}:
            blockers.append("stale_data")
        return DataGateResult(not blockers, quality, freshness.status, tuple(blockers))

    def validate(self, *, symbol: str, timeframe: str, data: Sequence[Candle]) -> Sequence[Candle]:
        result = self.inspect(symbol=symbol, timeframe=timeframe, data=data)
        if not result.accepted:
            raise ValueError("Market data rejected: " + ", ".join(result.blockers))
        return data


__all__ = ["DataGateResult", "MarketDataIntelligenceGate"]
