from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

@dataclass(frozen=True, slots=True)
class BreakoutResult:
    direction: str
    breakout: bool
    false_breakout: bool
    strength: float

class BreakoutEngine:
    def analyze(self, highs: Sequence[float], lows: Sequence[float], closes: Sequence[float], lookback: int = 5) -> BreakoutResult:
        if not (len(highs) == len(lows) == len(closes)) or len(closes) <= lookback:
            raise ValueError("insufficient aligned observations")
        resistance = max(highs[-lookback-1:-1])
        support = min(lows[-lookback-1:-1])
        c, h, l = closes[-1], highs[-1], lows[-1]
        up = h > resistance
        down = l < support
        false_up = up and c <= resistance
        false_down = down and c >= support
        if false_up:
            return BreakoutResult("BEARISH", True, True, min(1.0, (h - c) / max(abs(h), 1e-12)))
        if false_down:
            return BreakoutResult("BULLISH", True, True, min(1.0, (c - l) / max(abs(l), 1e-12)))
        if c > resistance:
            return BreakoutResult("BULLISH", True, False, min(1.0, (c - resistance) / max(abs(resistance), 1e-12)))
        if c < support:
            return BreakoutResult("BEARISH", True, False, min(1.0, (support - c) / max(abs(support), 1e-12)))
        return BreakoutResult("NEUTRAL", False, False, 0.0)
