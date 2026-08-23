from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Sequence

from .analysis_runtime import AnalysisEvidence, MultiTimeframeEvidence


@dataclass(frozen=True)
class WeightedEvidence:
    evidence: AnalysisEvidence
    weight: float
    contribution: float


@dataclass(frozen=True)
class Scenario:
    name: str
    probability: float
    activation: str
    invalidation: str


@dataclass(frozen=True)
class IntelligenceDecision:
    decision: str
    score: float
    confidence: float
    disagreement: float
    evidence: tuple[WeightedEvidence, ...]
    scenarios: tuple[Scenario, ...]
    reasons: tuple[str, ...]


class AdvancedFusion:
    def __init__(self, static_weights: dict[str, float] | None = None) -> None:
        self.static_weights = static_weights or {}

    def fuse(self, result: MultiTimeframeEvidence, data_quality: float = 100.0) -> IntelligenceDecision:
        items = []
        for evidence in result.evidence:
            weight = max(0.0, self.static_weights.get(evidence.analyzer, 1.0))
            contribution = weight * evidence.strength * evidence.confidence * evidence.quality / 10000.0
            items.append(WeightedEvidence(evidence, weight, contribution))
        if not items:
            return IntelligenceDecision("NO TRADE", 0.0, 0.0, 100.0, (), (), ("no_valid_evidence",))
        signed = sum(x.contribution * (1 if x.evidence.direction == "BUY" else -1 if x.evidence.direction == "SELL" else 0) for x in items)
        total = sum(x.weight * max(x.evidence.strength, 1.0) for x in items)
        score = max(-100.0, min(100.0, signed / total * 100.0)) if total else 0.0
        directions = [x.evidence.direction for x in items if x.evidence.direction in {"BUY", "SELL"}]
        disagreement = 0.0 if not directions else 100.0 * (1.0 - max(directions.count("BUY"), directions.count("SELL")) / len(directions))
        confidence = max(0.0, min(100.0, 0.55 * (100.0 - disagreement) + 0.25 * data_quality + 0.20 * (100.0 - result.conflicts.__len__() * 50.0)))
        decision = "NO TRADE" if data_quality < 70 or disagreement >= 60 or confidence < 55 else ("BUY" if score > 20 else "SELL" if score < -20 else "WAIT")
        scenarios = (
            Scenario("bullish", max(0.0, min(1.0, (score + 100) / 200)), "bullish evidence persists", "bullish thesis invalidated"),
            Scenario("bearish", max(0.0, min(1.0, (100 - score) / 200)), "bearish evidence persists", "bearish thesis invalidated"),
            Scenario("neutral", max(0.0, 1.0 - abs(score) / 100), "directional edge disappears", "new directional evidence appears"),
        )
        reasons = tuple(x.evidence.analyzer + ":" + x.evidence.direction for x in items)
        return IntelligenceDecision(decision, score, confidence, disagreement, tuple(items), scenarios, reasons)
