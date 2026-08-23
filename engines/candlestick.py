from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

@dataclass(frozen=True, slots=True)
class CandlePattern:
    name: str
    direction: str
    strength: float

class CandlestickEngine:
    def detect(self, opens: Sequence[float], highs: Sequence[float], lows: Sequence[float], closes: Sequence[float]) -> tuple[CandlePattern, ...]:
        if not (len(opens) == len(highs) == len(lows) == len(closes)) or not closes:
            raise ValueError("aligned OHLC observations required")
        o, h, l, c = opens[-1], highs[-1], lows[-1], closes[-1]
        body = abs(c - o)
        upper = h - max(o, c)
        lower = min(o, c) - l
        rng = max(h - l, 1e-12)
        out: list[CandlePattern] = []
        if body / rng <= 0.1:
            out.append(CandlePattern("DOJI", "NEUTRAL", 1 - body / rng))
        if lower >= 2 * max(body, 1e-12) and upper <= max(body, 1e-12):
            out.append(CandlePattern("HAMMER", "BULLISH", min(1.0, lower / rng)))
        if upper >= 2 * max(body, 1e-12) and lower <= max(body, 1e-12):
            out.append(CandlePattern("SHOOTING_STAR", "BEARISH", min(1.0, upper / rng)))
        return tuple(out)
