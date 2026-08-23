from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from strategy.contracts import StrategyContext, StrategyDecision
from strategy.registry import StrategyRegistry


@dataclass(frozen=True)
class StrategyRun:
    context: StrategyContext
    decisions: tuple[StrategyDecision, ...]
    errors: tuple[StrategyDecision, ...] = ()

    @property
    def successful(self) -> tuple[StrategyDecision, ...]:
        return tuple(decision for decision in self.decisions if decision.action.upper() not in {"ERROR", "FAILED"})


class StrategyOrchestrator:
    """Runs strategies with per-strategy isolation and deterministic ordering."""

    def __init__(self, registry: StrategyRegistry) -> None:
        self.registry = registry

    def run(self, context: StrategyContext, strategies: Iterable[str] | None = None) -> StrategyRun:
        names = tuple(strategies) if strategies is not None else self.registry.names()
        decisions: list[StrategyDecision] = []
        errors: list[StrategyDecision] = []
        for name in names:
            try:
                strategy = self.registry.create(name)
                decision = strategy.evaluate(context)
                if not isinstance(decision, StrategyDecision):
                    raise TypeError(f"Strategy {name!r} returned an invalid decision")
                decisions.append(decision)
            except Exception as exc:
                errors.append(
                    StrategyDecision(
                        strategy=str(name),
                        action="ERROR",
                        confidence=0.0,
                        reason=f"{type(exc).__name__}: {exc}",
                    )
                )
        return StrategyRun(context=context, decisions=tuple(decisions), errors=tuple(errors))
