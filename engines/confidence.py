from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class ConfidenceResult:
    score: float
    disagreement: float
    blocked: bool

class ConfidenceEngine:
    def calculate(self, agreement: float, data_quality: float, historical_quality: float, disagreement: float, regime_confidence: float) -> ConfidenceResult:
        values = [max(0.0, min(1.0, x)) for x in (agreement, data_quality, historical_quality, regime_confidence)]
        base = sum(values) / len(values)
        score = max(0.0, min(1.0, base * (1.0 - max(0.0, min(1.0, disagreement)))))
        blocked = score < 0.35 or disagreement >= 0.75 or data_quality < 0.5
        return ConfidenceResult(score, disagreement, blocked)
