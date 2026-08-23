from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True, slots=True)
class FusionResult:
    decision: str
    score: float
    agreement: float
    conflict: bool


class AnalysisFusionEngine:
    def combine(self, directions: Sequence[str], weights: Sequence[float] | None = None) -> FusionResult:
        if not directions:
            return FusionResult("NO_TRADE", 0.0, 0.0, True)
        if weights is None:
            weights = [1.0] * len(directions)
        if len(weights) != len(directions) or any(w < 0 for w in weights):
            raise ValueError("weights must align and be non-negative")
        total = sum(weights)
        if total <= 0:
            return FusionResult("NO_TRADE", 0.0, 0.0, True)
        signed = sum((1 if d == "BULLISH" else -1 if d == "BEARISH" else 0) * w for d, w in zip(directions, weights))
        score = signed / total
        agreement = abs(score)
        conflict = any(d == "BULLISH" for d in directions) and any(d == "BEARISH" for d in directions)
        if conflict and agreement < 0.35:
            decision = "NO_TRADE"
        elif score > 0.2:
            decision = "BUY"
        elif score < -0.2:
            decision = "SELL"
        else:
            decision = "WAIT"
        return FusionResult(decision, score, agreement, conflict)
