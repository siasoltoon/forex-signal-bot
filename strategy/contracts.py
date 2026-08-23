from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from analysis.contracts import AnalysisRun


@dataclass(frozen=True)
class StrategyContext:
    symbol: str
    timeframe: str
    analysis: AnalysisRun
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StrategyDecision:
    strategy: str
    action: str
    confidence: float
    reason: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)


class Strategy(Protocol):
    name: str

    def evaluate(self, context: StrategyContext) -> StrategyDecision:
        ...


class StrategyFactory(Protocol):
    def __call__(self) -> Strategy:
        ...
