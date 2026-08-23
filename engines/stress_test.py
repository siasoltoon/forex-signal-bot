from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True, slots=True)
class StressResult:
    worst_case: float
    breached: bool


class StressTestEngine:
    def run(self, exposures: Sequence[float], shocks: Sequence[float], loss_limit: float) -> StressResult:
        if len(exposures) != len(shocks) or loss_limit < 0:
            raise ValueError("aligned exposures/shocks and non-negative loss limit required")
        worst = sum(abs(e) * max(0.0, s) for e, s in zip(exposures, shocks))
        return StressResult(worst, worst > loss_limit)
