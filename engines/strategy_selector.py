from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True, slots=True)
class StrategyCandidate:
    name: str
    direction: str
    score: float
    regime: str
    enabled: bool = True


class StrategySelector:
    """Selects strategies from declared evidence; never invents market data."""

    def rank(self, candidates: Sequence[StrategyCandidate], regime: str | None = None) -> tuple[StrategyCandidate, ...]:
        filtered = [c for c in candidates if c.enabled and (regime is None or c.regime == regime)]
        return tuple(sorted(filtered, key=lambda c: c.score, reverse=True))

    def best(self, candidates: Sequence[StrategyCandidate], regime: str | None = None) -> StrategyCandidate | None:
        ranked = self.rank(candidates, regime)
        return ranked[0] if ranked else None

    def from_scores(self, scores: Mapping[str, float], direction: str, regime: str) -> tuple[StrategyCandidate, ...]:
        return tuple(StrategyCandidate(name, direction, float(score), regime) for name, score in scores.items())
