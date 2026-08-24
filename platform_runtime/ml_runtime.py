from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss
from sklearn.model_selection import TimeSeriesSplit


@dataclass(frozen=True)
class ModelOutput:
    model_name: str
    version: str
    probability: float
    calibrated: bool


@dataclass(frozen=True)
class Evaluation:
    accuracy: float
    log_loss: float
    samples: int


class ProbabilisticModel:
    def __init__(self, name: str, version: str = "1") -> None:
        self.name = name
        self.version = version
        self.model = LogisticRegression(max_iter=2000)
        self.calibrated_model = None
        self.is_calibrated = False

    def fit(self, features: Sequence[Sequence[float]], labels: Sequence[int]) -> None:
        x = np.asarray(features, dtype=float)
        y = np.asarray(labels, dtype=int)
        if len(x) < 10 or len(np.unique(y)) < 2:
            raise ValueError("real training data with at least two classes is required")
        self.model.fit(x, y)

    def calibrate(self, features: Sequence[Sequence[float]], labels: Sequence[int]) -> None:
        x = np.asarray(features, dtype=float)
        y = np.asarray(labels, dtype=int)
        if len(x) < 20 or len(np.unique(y)) < 2:
            raise ValueError("calibration requires sufficient real OOS data")
        self.calibrated_model = CalibratedClassifierCV(self.model, method="sigmoid", cv=TimeSeriesSplit(n_splits=3))
        self.calibrated_model.fit(x, y)
        self.is_calibrated = True

    def predict(self, features: Sequence[float]) -> ModelOutput:
        model = self.calibrated_model or self.model
        probability = float(model.predict_proba([features])[0][1])
        return ModelOutput(self.name, self.version, probability, self.is_calibrated)

    def evaluate(self, features: Sequence[Sequence[float]], labels: Sequence[int]) -> Evaluation:
        model = self.calibrated_model or self.model
        x = np.asarray(features, dtype=float)
        y = np.asarray(labels, dtype=int)
        probabilities = model.predict_proba(x)[:, 1]
        predictions = (probabilities >= 0.5).astype(int)
        return Evaluation(float(accuracy_score(y, predictions)), float(log_loss(y, probabilities)), len(y))


class ChampionChallenger:
    def __init__(self, champion: ProbabilisticModel | None = None) -> None:
        self.champion = champion

    def promote_if_better(self, challenger: ProbabilisticModel, features: Sequence[Sequence[float]], labels: Sequence[int], minimum_accuracy_gain: float = 0.0) -> bool:
        challenger_score = challenger.evaluate(features, labels)
        if self.champion is None:
            self.champion = challenger
            return True
        champion_score = self.champion.evaluate(features, labels)
        if challenger_score.accuracy >= champion_score.accuracy + minimum_accuracy_gain and challenger_score.log_loss <= champion_score.log_loss:
            self.champion = challenger
            return True
        return False
