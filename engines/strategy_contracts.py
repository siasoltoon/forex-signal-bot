from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence


class StrategyState(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    RETIRED = "RETIRED"
    CHALLENGER = "CHALLENGER"


@dataclass(frozen=True)
class StrategyDNA:
    strategy_id: str
    market: str
    timeframes: Sequence[str]
    regime: str
    entry_conditions: Sequence[str]
    exit_conditions: Sequence[str]
    invalidation_conditions: Sequence[str]
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StrategyScore:
    performance: float
    stability: float
    drawdown: float
    risk_adjusted_return: float

    @property
    def composite(self) -> float:
        return (
            self.performance * 0.35
            + self.stability * 0.25
            + self.drawdown * 0.15
            + self.risk_adjusted_return * 0.25
        )


@dataclass
class Strategy:
    dna: StrategyDNA
    state: StrategyState = StrategyState.ACTIVE
    score: StrategyScore | None = None


class StrategyRegistry:
    def __init__(self) -> None:
        self._strategies: dict[str, Strategy] = {}

    def register(self, strategy: Strategy) -> None:
        self._strategies[strategy.dna.strategy_id] = strategy

    def get(self, strategy_id: str) -> Strategy | None:
        return self._strategies.get(strategy_id)

    def active(self) -> list[Strategy]:
        return [s for s in self._strategies.values() if s.state is StrategyState.ACTIVE]

    def ranked(self) -> list[Strategy]:
        return sorted(
            self.active(),
            key=lambda strategy: strategy.score.composite if strategy.score else float("-inf"),
            reverse=True,
        )
