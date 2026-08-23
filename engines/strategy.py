from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum


class StrategyState(StrEnum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CHALLENGER = "CHALLENGER"
    RETIRED = "RETIRED"


@dataclass(frozen=True, slots=True)
class StrategyDefinition:
    key: str
    name: str
    markets: tuple[str, ...]
    timeframes: tuple[str, ...]
    regimes: tuple[str, ...]
    state: StrategyState = StrategyState.ACTIVE
    historical_expectancy: float = 0.0
    stability: float = 0.0
    max_drawdown: float = 0.0

    @property
    def ranking_score(self) -> float:
        drawdown_penalty = max(0.0, min(1.0, self.max_drawdown))
        return self.historical_expectancy * 0.5 + self.stability * 0.35 + (1 - drawdown_penalty) * 0.15


class StrategyEngine:
    def __init__(self, strategies: tuple[StrategyDefinition, ...] = ()) -> None:
        self._strategies = {strategy.key: strategy for strategy in strategies}

    def register(self, strategy: StrategyDefinition) -> None:
        if strategy.key in self._strategies:
            raise ValueError(f"duplicate strategy: {strategy.key}")
        self._strategies[strategy.key] = strategy

    def rank(self, *, market: str | None = None, timeframe: str | None = None, regime: str | None = None) -> tuple[StrategyDefinition, ...]:
        candidates = [item for item in self._strategies.values() if item.state == StrategyState.ACTIVE]
        if market:
            candidates = [item for item in candidates if not item.markets or market in item.markets]
        if timeframe:
            candidates = [item for item in candidates if not item.timeframes or timeframe in item.timeframes]
        if regime:
            candidates = [item for item in candidates if not item.regimes or regime in item.regimes]
        return tuple(sorted(candidates, key=lambda item: item.ranking_score, reverse=True))

    def retire(self, key: str) -> None:
        self._strategies[key] = replace(self._strategies[key], state=StrategyState.RETIRED)
