from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EvaluationSnapshot:
    model_id: str
    score: float
    drawdown: float
    samples: int


@dataclass(frozen=True, slots=True)
class EvaluationStatus:
    healthy: bool
    reason: str


class ContinuousEvaluator:
    """Evaluates supplied snapshots and never mutates deployment state."""

    def __init__(self, *, minimum_samples: int = 1, minimum_score: float = 0.0, maximum_drawdown: float = 1.0) -> None:
        if minimum_samples < 0 or maximum_drawdown < 0:
            raise ValueError("evaluation limits must be non-negative")
        self.minimum_samples = minimum_samples
        self.minimum_score = minimum_score
        self.maximum_drawdown = maximum_drawdown

    def evaluate(self, snapshot: EvaluationSnapshot) -> EvaluationStatus:
        if snapshot.samples < self.minimum_samples:
            return EvaluationStatus(False, "insufficient_samples")
        if snapshot.drawdown > self.maximum_drawdown:
            return EvaluationStatus(False, "drawdown_limit")
        if snapshot.score < self.minimum_score:
            return EvaluationStatus(False, "score_below_threshold")
        return EvaluationStatus(True, "healthy")
