from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True, slots=True)
class StructureResult:
    direction: str
    trend_strength: float
    higher_highs: int
    lower_lows: int
    breakout: bool
    rejection: bool


class MarketStructureEngine:
    def analyze(self, highs: Sequence[float], lows: Sequence[float]) -> StructureResult:
        if len(highs) != len(lows) or len(highs) < 3:
            raise ValueError("highs and lows require at least three aligned observations")
        hh = sum(1 for a, b in zip(highs, highs[1:]) if b > a)
        ll = sum(1 for a, b in zip(lows, lows[1:]) if b < a)
        total = max(1, len(highs) - 1)
        strength = min(1.0, abs(hh - ll) / total)
        direction = "BULLISH" if hh > ll else "BEARISH" if ll > hh else "NEUTRAL"
        breakout = hh >= max(2, total // 2) or ll >= max(2, total // 2)
        rejection = hh > 0 and ll > 0 and abs(hh - ll) <= 1
        return StructureResult(direction, strength, hh, ll, breakout, rejection)
