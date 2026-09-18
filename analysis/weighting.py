from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite


class WeightMode(str, Enum):
    STATIC = "static"
    DYNAMIC = "dynamic"
    REGIME = "regime"
    PERFORMANCE = "performance"


@dataclass(frozen=True, slots=True)
class WeightedEvidence:
    source: str
    direction: str
    strength: float
    quality: float
    weight: float = 1.0

    @property
    def effective_weight(self) -> float:
        return max(0.0, self.weight) * max(0.0, min(1.0, self.quality))


@dataclass(frozen=True, slots=True)
class Consensus:
    direction: str
    score: float
    disagreement: float
    evidence_count: int


class EvidenceAggregator:
    """Weighted consensus without majority-vote shortcuts."""

    def aggregate(self, evidence: tuple[WeightedEvidence, ...]) -> Consensus:
        if not evidence:
            return Consensus("NEUTRAL", 0.0, 1.0, 0)
        totals: dict[str, float] = {}
        total = 0.0
        for item in evidence:
            strength = max(-1.0, min(1.0, item.strength))
            weight = item.effective_weight
            if not isfinite(strength) or not isfinite(weight):
                continue
            totals[item.direction.upper()] = totals.get(item.direction.upper(), 0.0) + abs(strength) * weight
            total += abs(strength) * weight
        if total <= 0.0:
            return Consensus("NEUTRAL", 0.0, 1.0, len(evidence))
        direction, dominant = max(totals.items(), key=lambda pair: pair[1])
        score = dominant / total
        disagreement = 1.0 - score
        return Consensus(direction, score, disagreement, len(evidence))
