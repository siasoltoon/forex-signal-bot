from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping

from analysis.contracts import AnalysisRun


class DecisionAction(StrEnum):
    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"
    NO_TRADE = "NO_TRADE"


@dataclass(frozen=True, slots=True)
class AnalysisEvidence:
    name: str
    direction: str
    strength: float
    quality: float
    confidence: float
    weight: float
    timeframe: str | None = None

    @property
    def contribution(self) -> float:
        direction = self.direction.upper()
        sign = 1.0 if direction in {"BUY", "BULLISH", "LONG"} else -1.0 if direction in {"SELL", "BEARISH", "SHORT"} else 0.0
        return sign * self.strength * self.quality * self.confidence * self.weight


@dataclass(frozen=True, slots=True)
class DecisionPolicy:
    minimum_confidence: float = 0.60
    minimum_quality: float = 0.50
    maximum_disagreement: float = 0.60
    no_trade_on_missing_data: bool = True


@dataclass(frozen=True, slots=True)
class DecisionResult:
    action: DecisionAction
    score: float
    confidence: float
    disagreement: float
    reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    evidence: tuple[AnalysisEvidence, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)
