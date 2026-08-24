from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class MarketRegime(StrEnum):
    TREND = "TREND"
    RANGE = "RANGE"
    BREAKOUT = "BREAKOUT"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"
    ACCUMULATION = "ACCUMULATION"
    DISTRIBUTION = "DISTRIBUTION"
    EXPANSION = "EXPANSION"
    CONTRACTION = "CONTRACTION"
    CRISIS = "CRISIS"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class RegimeEvidence:
    regime: MarketRegime
    confidence: float
    reason: str


class RegimeEngine:
    def select(self, evidence: tuple[RegimeEvidence, ...]) -> MarketRegime:
        if not evidence:
            return MarketRegime.UNKNOWN
        valid = [item for item in evidence if 0 <= item.confidence <= 1]
        if not valid:
            return MarketRegime.UNKNOWN
        return max(valid, key=lambda item: item.confidence).regime
