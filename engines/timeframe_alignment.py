from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

@dataclass(frozen=True, slots=True)
class AlignmentResult:
    aligned: bool
    dominant_direction: str
    disagreement: float

class TimeframeAlignmentEngine:
    def evaluate(self, directions: Mapping[str, str], priority: Sequence[str] = ("1D", "4H", "1H", "15M", "5M", "1M")) -> AlignmentResult:
        if not directions:
            return AlignmentResult(False, "NEUTRAL", 1.0)
        scores = {"BULLISH": 1, "BEARISH": -1, "NEUTRAL": 0}
        ordered = [directions[k] for k in priority if k in directions]
        if not ordered:
            ordered = list(directions.values())
        numeric = [scores.get(x, 0) for x in ordered]
        total = sum(numeric)
        dominant = "BULLISH" if total > 0 else "BEARISH" if total < 0 else "NEUTRAL"
        disagreement = 1 - abs(total) / max(1, len(numeric))
        return AlignmentResult(disagreement < 0.5, dominant, disagreement)
