from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
from market.provider_contracts import Candle

@dataclass(frozen=True, slots=True)
class DataQuality:
    score: float
    valid: bool
    gaps: int
    duplicates: int
    stale: bool
    anomalies: int

class MarketDataValidator:
    def validate(self, candles: Sequence[Candle], expected_interval: int | None = None, latest_timestamp: int | None = None) -> DataQuality:
        gaps = duplicates = anomalies = 0
        previous = None
        for candle in candles:
            if candle.high < max(candle.open, candle.close) or candle.low > min(candle.open, candle.close) or candle.low > candle.high:
                anomalies += 1
            if previous is not None:
                if candle.timestamp == previous:
                    duplicates += 1
                elif expected_interval and candle.timestamp - previous > expected_interval:
                    gaps += 1
            previous = candle.timestamp
        stale = bool(latest_timestamp is not None and candles and candles[-1].timestamp < latest_timestamp)
        penalty = 0.25 * gaps + 0.25 * duplicates + 0.25 * anomalies + (0.25 if stale else 0)
        score = max(0.0, 1.0 - penalty)
        return DataQuality(score, bool(candles) and score >= 0.75, gaps, duplicates, stale, anomalies)
