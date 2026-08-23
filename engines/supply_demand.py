from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True, slots=True)
class Zone:
    kind: str
    lower: float
    upper: float
    strength: float


class SupplyDemandEngine:
    def detect(self, highs: Sequence[float], lows: Sequence[float]) -> tuple[Zone, ...]:
        if len(highs) != len(lows) or len(highs) < 3:
            raise ValueError("aligned high/low observations required")
        zones: list[Zone] = []
        for high, low in zip(highs[-3:], lows[-3:]):
            if high <= low:
                continue
            midpoint = (high + low) / 2
            width = max((high - low) * 0.25, 1e-12)
            zones.append(Zone("SUPPLY", midpoint, high, min(1.0, width / max(abs(high), 1e-12))))
            zones.append(Zone("DEMAND", low, midpoint, min(1.0, width / max(abs(low), 1e-12))))
        return tuple(zones)
