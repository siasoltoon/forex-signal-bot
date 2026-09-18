from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence


class ModelStage(str, Enum):
    TRAINING = "TRAINING"
    VALIDATION = "VALIDATION"
    CHAMPION = "CHAMPION"
    CHALLENGER = "CHALLENGER"
    RETIRED = "RETIRED"


@dataclass(frozen=True)
class ModelDescriptor:
    model_id: str
    version: str
    family: str
    stage: ModelStage
    features: Sequence[str] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelEvaluation:
    model_id: str
    version: str
    score: float
    calibrated: bool
    leakage_detected: bool = False
    metrics: Mapping[str, float] = field(default_factory=dict)


class ModelRegistry:
    def __init__(self) -> None:
        self._models: dict[str, ModelDescriptor] = {}

    def register(self, model: ModelDescriptor) -> None:
        self._models[f"{model.model_id}:{model.version}"] = model

    def champion(self, model_id: str) -> ModelDescriptor | None:
        for model in self._models.values():
            if model.model_id == model_id and model.stage is ModelStage.CHAMPION:
                return model
        return None

    def challengers(self, model_id: str) -> list[ModelDescriptor]:
        return [m for m in self._models.values() if m.model_id == model_id and m.stage is ModelStage.CHALLENGER]
