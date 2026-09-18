from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelScore:
    model_id: str
    score: float
    drawdown: float = 0.0
    stability: float = 0.0


@dataclass(frozen=True, slots=True)
class PromotionDecision:
    promoted: bool
    active_model: str
    reason: str


class ChampionChallenger:
    """Deterministic promotion policy; deployment remains an external concern."""

    def __init__(self, *, minimum_improvement: float = 0.0, maximum_drawdown: float = 1.0) -> None:
        if minimum_improvement < 0 or maximum_drawdown < 0:
            raise ValueError("lifecycle limits must be non-negative")
        self.minimum_improvement = minimum_improvement
        self.maximum_drawdown = maximum_drawdown

    def evaluate(self, champion: ModelScore, challenger: ModelScore) -> PromotionDecision:
        if challenger.drawdown > self.maximum_drawdown:
            return PromotionDecision(False, champion.model_id, "challenger_drawdown_limit")
        improvement = challenger.score - champion.score
        if improvement < self.minimum_improvement:
            return PromotionDecision(False, champion.model_id, "insufficient_improvement")
        return PromotionDecision(True, challenger.model_id, "challenger_passed")
