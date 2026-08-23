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
    take_profit: tuple[float, ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= self.probability <= 1.0:
            raise ValueError("probability must be between 0 and 1")


__all__ = ["Scenario", "ScenarioType"]
