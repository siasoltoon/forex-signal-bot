from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True, slots=True)
class VolumeResult:
    direction: str
    relative_volume: float
    vwap: float
    above_vwap: bool


class VolumeVWAPEngine:
    def analyze(self, highs: Sequence[float], lows: Sequence[float], closes: Sequence[float], volumes: Sequence[float]) -> VolumeResult:
        if not (len(highs) == len(lows) == len(closes) == len(volumes)) or not closes:
            raise ValueError("aligned OHLCV observations required")
        total_volume = sum(max(v, 0.0) for v in volumes)
        if total_volume <= 0:
            raise ValueError("positive volume required")
        typical = [(h + l + c) / 3 for h, l, c in zip(highs, lows, closes)]
        vwap = sum(p * max(v, 0.0) for p, v in zip(typical, volumes)) / total_volume
        recent = max(volumes[-1], 0.0)
        baseline = sum(max(v, 0.0) for v in volumes[:-1]) / max(1, len(volumes) - 1)
        relative = recent / max(baseline, 1e-12)
        direction = "BULLISH" if closes[-1] > vwap else "BEARISH" if closes[-1] < vwap else "NEUTRAL"
        return VolumeResult(direction, relative, vwap, closes[-1] >= vwap)
