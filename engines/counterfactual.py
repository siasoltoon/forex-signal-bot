from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Mapping

@dataclass(frozen=True, slots=True)
class CounterfactualResult:
    baseline: float
    alternative: float
    delta: float
    condition: str

class CounterfactualEngine:
    def evaluate(self, baseline: float, scenarios: Mapping[str, Callable[[], float]]) -> tuple[CounterfactualResult, ...]:
        out = []
        for condition, fn in scenarios.items():
            alternative = float(fn())
            out.append(CounterfactualResult(baseline, alternative, alternative - baseline, condition))
        return tuple(out)
