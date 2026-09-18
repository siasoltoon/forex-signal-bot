from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MarketRegime(str, Enum):
    TREND = "trend"
    RANGE = "range"
    BREAKOUT = "breakout"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    ACCUMULATION = "accumulation"
    DISTRIBUTION = "distribution"
    EXPANSION = "expansion"
    CONTRACTION = "contraction"
    CRISIS = "crisis"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class RegimeEvidence:
    name: str
    score: float
    quality: float = 1.0


@dataclass(frozen=True, slots=True)
class RegimeResult:
    regime: MarketRegime
    confidence: float
    evidence: tuple[RegimeEvidence, ...] = ()


class MarketRegimeEngine:
    """Deterministic regime classifier over already-computed evidence.

    It deliberately does not fetch market data or invent missing observations.
    """

    def classify(self, evidence: tuple[RegimeEvidence, ...]) -> RegimeResult:
        if not evidence:
            return RegimeResult(MarketRegime.UNKNOWN, 0.0)

        totals: dict[str, float] = {}
        for item in evidence:
            score = max(0.0, min(1.0, item.score))
            quality = max(0.0, min(1.0, item.quality))
            if score * quality <= 0:
                continue
            totals[item.name.lower()] = totals.get(item.name.lower(), 0.0) + score * quality

        if not totals:
            return RegimeResult(MarketRegime.UNKNOWN, 0.0, evidence)

        name, dominant = max(totals.items(), key=lambda pair: pair[1])
        total = sum(totals.values())
        confidence = dominant / total if total else 0.0
        try:
            regime = MarketRegime(name)
        except ValueError:
            regime = MarketRegime.UNKNOWN
        return RegimeResult(regime, confidence, evidence)
