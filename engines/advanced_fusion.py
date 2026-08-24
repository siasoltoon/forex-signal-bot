from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True, slots=True)
class Evidence:
    name: str
    direction: str
    strength: float
    quality: float = 1.0
    static_weight: float = 1.0
    dynamic_weight: float = 1.0
    regime_weight: float = 1.0
    performance_weight: float = 1.0

@dataclass(frozen=True, slots=True)
class FusionResult:
    score: float
    agreement: float
    disagreement: float
    effective_weight: float

class AdvancedFusionEngine:
    def combine(self, evidence: Iterable[Evidence], regime: str | None = None) -> FusionResult:
        items = list(evidence)
        if not items:
            return FusionResult(0.0, 0.0, 1.0, 0.0)
        signed = {"BULLISH": 1.0, "BEARISH": -1.0, "NEUTRAL": 0.0}
        weighted = 0.0
        total = 0.0
        for item in items:
            w = max(0.0, item.static_weight * item.dynamic_weight * item.regime_weight * item.performance_weight * item.quality)
            weighted += signed.get(item.direction, 0.0) * max(0.0, min(1.0, item.strength)) * w
            total += w
        score = weighted / total if total else 0.0
        agreement = abs(sum(signed.get(x.direction, 0.0) for x in items)) / len(items)
        disagreement = 1.0 - agreement
        return FusionResult(score, agreement, disagreement, total)
