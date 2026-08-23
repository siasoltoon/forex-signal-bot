from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True, slots=True)
class MomentumResult:
    direction: str
    strength: float
    acceleration: float


class MomentumEngine:
    def analyze(self, closes: Sequence[float], period: int = 5) -> MomentumResult:
        if period < 1 or len(closes) <= period:
            raise ValueError("insufficient closes for momentum")
        change = closes[-1] - closes[-1 - period]
        previous = closes[-1 - period] - closes[-1 - 2 * period] if len(closes) > 2 * period else change
        acceleration = change - previous
        scale = max(abs(closes[-1 - period]), 1e-12)
        strength = min(1.0, abs(change / scale))
        direction = "BULLISH" if change > 0 else "BEARISH" if change < 0 else "NEUTRAL"
        return MomentumResult(direction, strength, acceleration)
