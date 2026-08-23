from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True, slots=True)
class RegimeResult:
    regime: str
    confidence: float
    volatility_state: str


class MarketRegimeEngine:
    def classify(self, closes: Sequence[float], volatility: Sequence[float]) -> RegimeResult:
        if len(closes) < 4 or not volatility:
            raise ValueError("insufficient observations")
        returns = [b - a for a, b in zip(closes, closes[1:])]
        direction = sum(1 if x > 0 else -1 if x < 0 else 0 for x in returns)
        vol = sum(volatility) / len(volatility)
        if direction >= 2:
            regime = "TREND_UP"
        elif direction <= -2:
            regime = "TREND_DOWN"
        else:
            regime = "RANGE"
        volatility_state = "HIGH" if vol > 0.02 else "LOW" if vol < 0.005 else "NORMAL"
        confidence = min(1.0, abs(direction) / max(1, len(returns)))
        return RegimeResult(regime, confidence, volatility_state)
