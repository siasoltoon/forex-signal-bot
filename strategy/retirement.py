from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RetirementDecision:
    strategy_id: str
    retired: bool
    reason: str


class StrategyRetirementPolicy:
    def __init__(self, *, minimum_score: float = 0.0, maximum_drawdown: float = 1.0, minimum_trades: int = 0) -> None:
        if maximum_drawdown < 0 or minimum_trades < 0:
            raise ValueError("retirement limits must be non-negative")
        self.minimum_score = minimum_score
        self.maximum_drawdown = maximum_drawdown
        self.minimum_trades = minimum_trades

    def evaluate(self, strategy_id: str, *, score: float, drawdown: float, trades: int) -> RetirementDecision:
        if trades < self.minimum_trades:
            return RetirementDecision(strategy_id, False, "insufficient_evidence")
        if drawdown > self.maximum_drawdown:
            return RetirementDecision(strategy_id, True, "drawdown_limit")
        if score < self.minimum_score:
            return RetirementDecision(strategy_id, True, "score_below_threshold")
        return RetirementDecision(strategy_id, False, "healthy")
