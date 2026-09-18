from __future__ import annotations

from dataclasses import dataclass
import random


@dataclass(frozen=True, slots=True)
class MonteCarloSummary:
    runs: int
    seed: int
    average_total: float
    worst_total: float
    best_total: float


class MonteCarloSimulator:
    def simulate(self, pnls: tuple[float, ...], *, runs: int = 1000, seed: int = 0) -> MonteCarloSummary:
        if runs <= 0:
            raise ValueError("runs must be positive")
        rng = random.Random(seed)
        totals: list[float] = []
        source = tuple(pnls)
        if not source:
            return MonteCarloSummary(runs, seed, 0.0, 0.0, 0.0)
        for _ in range(runs):
            shuffled = list(source)
            rng.shuffle(shuffled)
            totals.append(sum(shuffled))
        return MonteCarloSummary(runs, seed, sum(totals) / len(totals), min(totals), max(totals))
