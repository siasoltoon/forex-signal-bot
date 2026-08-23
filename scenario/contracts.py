from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ScenarioType(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


@dataclass(frozen=True, slots=True)
class Scenario:
    kind: ScenarioType
    probability: float
    activation_condition: str
    invalidation_condition: str
    stop_loss: float | None = None
    take_profits: tuple[float, ...] = ()


__all__ = ["Scenario", "ScenarioType"]
