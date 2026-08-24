from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence

@dataclass(frozen=True, slots=True)
class EvaluationSplit:
    train: tuple
    validation: tuple
    test: tuple

class ResearchEvaluator:
    def split(self, observations: Sequence, train_ratio: float = .6, validation_ratio: float = .2) -> EvaluationSplit:
        if not 0 < train_ratio < 1 or not 0 <= validation_ratio < 1 or train_ratio + validation_ratio >= 1:
            raise ValueError("invalid split ratios")
        n = len(observations)
        a = int(n * train_ratio)
        b = a + int(n * validation_ratio)
        return EvaluationSplit(tuple(observations[:a]), tuple(observations[a:b]), tuple(observations[b:]))

    def detect_leakage(self, train: Sequence, test: Sequence) -> bool:
        return bool(set(map(repr, train)).intersection(map(repr, test)))

    def overfit_gap(self, train_score: float, test_score: float) -> float:
        return max(0.0, float(train_score) - float(test_score))
