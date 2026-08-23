from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from strategy.contracts import StrategyContext, StrategyDecision
from strategy.registry import StrategyRegistry


@dataclass(frozen=True)
class StrategyRun:
    context: StrategyContext
    decisions: tuple[StrategyDecision, ...]


class StrategyOrchestrator:
    """Runs registered strategies against a completed analysis run."""

    def __init__(self, registry: StrategyRegistry) -> None:
        self.registry = registry

    def run(self, context: StrategyContext, strategies: Iterable[str] | None = None) -> StrategyRun:
        names = tuple(strategies) if strategies is not None else self.registry.names()
        decisions: list[StrategyDecision] = []
        for name in names:
            strategy = self.registry.create(name)
            decision = strategy.evaluate(context)
            if not isinstance(decision, StrategyDecision):
                raise TypeError(f"Strategy {name!r} returned an invalid decision")
            decisions.append(decision)
        return StrategyRun(context=context, decisions=tuple(decisions))
