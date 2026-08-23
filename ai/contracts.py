from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ModelRole(str, Enum):
    PREDICTION = "PREDICTION"
    CLASSIFICATION = "CLASSIFICATION"
    REGIME = "REGIME"
    ANOMALY = "ANOMALY"
    VOLATILITY = "VOLATILITY"
    PATTERN = "PATTERN"
    JUDGE = "JUDGE"


@dataclass(frozen=True, slots=True)
class ModelPrediction:
    model: str
    role: ModelRole
    value: object
    confidence: float | None = None
    calibrated: bool = False


@dataclass(frozen=True, slots=True)
class ModelEvaluation:
    model: str
    sample_count: int
    metric: str
    value: float
    regime: str | None = None


@dataclass(frozen=True, slots=True)
class ModelRelease:
    model: str
    version: str
    champion: bool
    challenger: bool
    evaluation_required: bool = True


__all__ = ["ModelEvaluation", "ModelPrediction", "ModelRelease", "ModelRole"]
