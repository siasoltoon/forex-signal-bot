from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StrategyScore:
    strategy: str
    return_score: float
    stability: float
    drawdown: float
    trade_count: int

    @property
    def ranking_score(self) -> float:
        return self.return_score * max(0.0, self.stability) * max(0.0, 1.0 - self.drawdown)


class StrategyEvaluator:
    def rank(self, scores: tuple[StrategyScore, ...]) -> tuple[StrategyScore, ...]:
        return tuple(sorted(scores, key=lambda item: item.ranking_score, reverse=True))
