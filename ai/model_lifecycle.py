from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class ModelStage(str, Enum):
    CANDIDATE = "CANDIDATE"
    CHAMPION = "CHAMPION"
    RETIRED = "RETIRED"

@dataclass(frozen=True, slots=True)
class ModelScore:
    model_id: str
    score: float
    stability: float
    drawdown: float

class ModelLifecycle:
    def promote(self, candidate: ModelScore, champion: ModelScore | None, min_gain: float = .02) -> ModelStage:
        if champion is None or candidate.score >= champion.score + min_gain:
            return ModelStage.CHAMPION
        return ModelStage.CANDIDATE

    def should_rollback(self, champion: ModelScore, baseline_score: float, tolerance: float = .05) -> bool:
        return champion.score < baseline_score * (1.0 - tolerance)
