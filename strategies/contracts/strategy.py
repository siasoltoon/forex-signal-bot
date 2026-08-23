from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar, Mapping, Sequence

from analysis.contracts.context import AnalysisContext


@dataclass(frozen=True)
class StrategySetup:
    """A concrete trade/setup candidate produced by a strategy."""

    strategy_id: str
    direction: str
    entry: float | None = None
    stop_loss: float | None = None
    take_profit: Sequence[float] = field(default_factory=tuple)
    invalidation: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


class Strategy(ABC):
    """Contract for strategy plugins consuming analysis context."""

    strategy_id: ClassVar[str]
    version: ClassVar[str] = "1.0"

    @abstractmethod
    def supports(self, context: AnalysisContext) -> bool:
        raise NotImplementedError

    @abstractmethod
    def evaluate(self, context: AnalysisContext) -> StrategySetup | None:
        raise NotImplementedError
