from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Sequence

@dataclass(frozen=True, slots=True)
class VolatilityResult:
    value: float
    state: str
    percentile: float

class VolatilityEngine:
    def analyze(self, closes: Sequence[float], window: int = 10) -> VolatilityResult:
        if len(closes) <= window:
            raise ValueError("insufficient closes")
        returns = [(b - a) / max(abs(a), 1e-12) for a, b in zip(closes, closes[1:])]
        sample = returns[-window:]
        mean = sum(sample) / len(sample)
        variance = sum((x - mean) ** 2 for x in sample) / len(sample)
        value = sqrt(variance)
        state = "HIGH" if value > 0.02 else "LOW" if value < 0.005 else "NORMAL"
        historical = returns[:-window] or sample
        rank = sum(1 for x in historical if abs(x) <= value) / len(historical)
        return VolatilityResult(value, state, min(1.0, rank))
