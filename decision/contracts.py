from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


class DecisionAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"
    NO_TRADE = "NO_TRADE"


@dataclass(frozen=True, slots=True)
class DecisionEvidence:
    source: str
    direction: str
    strength: float
    weight: float = 1.0
    quality: float = 1.0
    reason: str = ""


@dataclass(frozen=True, slots=True)
class DecisionResult:
    action: DecisionAction
    score: float
    confidence: float
    disagreement: float
    blockers: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    @property
    def tradable(self) -> bool:
        return self.action in {DecisionAction.BUY, DecisionAction.SELL} and not self.blockers


__all__ = ["DecisionAction", "DecisionEvidence", "DecisionResult"]
