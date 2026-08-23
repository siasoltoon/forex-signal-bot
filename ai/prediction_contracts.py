from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Sequence

@dataclass(frozen=True, slots=True)
class ModelPrediction:
    model_id: str
    task: str
    value: float
    confidence: float
    metadata: dict[str, str]

class PredictionModel(Protocol):
    model_id: str
    def predict(self, features: Sequence[float]) -> ModelPrediction: ...
