from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

@dataclass(frozen=True, slots=True)
class WyckoffResult:
    phase: str
    direction: str
    confidence: float

class WyckoffEngine:
    def classify(self, closes: Sequence[float], volumes: Sequence[float]) -> WyckoffResult:
        if len(closes) < 6 or len(closes) != len(volumes):
            raise ValueError("aligned close/volume observations required")
        recent = closes[-3:]
        prior = closes[-6:-3]
        recent_change = recent[-1] - recent[0]
        prior_change = prior[-1] - prior[0]
        recent_vol = sum(volumes[-3:]) / 3
        prior_vol = sum(volumes[-6:-3]) / 3
        if abs(prior_change) < abs(recent_change) and recent_vol > prior_vol:
            phase = "MARKUP" if recent_change > 0 else "MARKDOWN"
        elif abs(recent_change) < abs(prior_change):
            phase = "ACCUMULATION" if prior_change <= 0 else "DISTRIBUTION"
        else:
            phase = "RANGE"
        direction = "BULLISH" if phase in {"ACCUMULATION", "MARKUP"} else "BEARISH" if phase in {"DISTRIBUTION", "MARKDOWN"} else "NEUTRAL"
        confidence = min(1.0, abs(recent_change) / max(abs(closes[-6]), 1e-12))
        return WyckoffResult(phase, direction, confidence)
