from __future__ import annotations

from dataclasses import dataclass
from random import Random
from statistics import mean, pstdev
from typing import Sequence


@dataclass(frozen=True)
class MonteCarloResult:
    trials: int
    mean_outcome: float
    p05: float
    p95: float


def monte_carlo(returns: Sequence[float], trials: int = 1000, seed: int = 7) -> MonteCarloResult:
    if not returns or trials <= 0:
        return MonteCarloResult(0, 0.0, 0.0, 0.0)
    rng = Random(seed)
    outcomes = []
    for _ in range(trials):
        shuffled = list(returns)
        rng.shuffle(shuffled)
        outcomes.append(sum(shuffled))
    outcomes.sort()
    return MonteCarloResult(trials, mean(outcomes), outcomes[max(0, int(trials * .05) - 1)], outcomes[min(trials - 1, int(trials * .95))])


@dataclass(frozen=True)
class ResearchIntegrity:
    leakage_detected: bool
    overfit_warning: bool
    reasons: tuple[str, ...]


def detect_integrity(train_ids: Sequence[str], test_ids: Sequence[str], parameter_count: int = 0, observations: int = 0) -> ResearchIntegrity:
    overlap = set(train_ids).intersection(test_ids)
    reasons: list[str] = []
    if overlap:
        reasons.append("train_test_overlap")
    if observations and parameter_count > observations / 10:
        reasons.append("high_parameter_to_observation_ratio")
    return ResearchIntegrity(bool(overlap), bool(reasons) and not bool(overlap), tuple(reasons))
