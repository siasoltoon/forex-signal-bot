from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True, slots=True)
class SMCResult:
    direction: str
    liquidity_sweep: bool
    displacement: bool
    imbalance: bool


class SMCEngine:
    def analyze(self, highs: Sequence[float], lows: Sequence[float], closes: Sequence[float]) -> SMCResult:
        if not (len(highs) == len(lows) == len(closes)) or len(closes) < 4:
            raise ValueError("aligned OHLC observations required")
        sweep_up = highs[-1] > max(highs[:-1]) and closes[-1] < highs[-1]
        sweep_down = lows[-1] < min(lows[:-1]) and closes[-1] > lows[-1]
        displacement = abs(closes[-1] - closes[-2]) > abs(closes[-2] - closes[-3])
        imbalance = abs(closes[-1] - closes[-2]) > 2 * max(abs(closes[-2] - closes[-3]), 1e-12)
        direction = "BEARISH" if sweep_up else "BULLISH" if sweep_down else "NEUTRAL"
        return SMCResult(direction, sweep_up or sweep_down, displacement, imbalance)
