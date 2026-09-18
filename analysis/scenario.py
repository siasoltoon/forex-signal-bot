from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ScenarioDirection(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass(frozen=True, slots=True)
class Scenario:
    direction: ScenarioDirection
    probability: float
    activation_condition: str
    invalidation_condition: str
    entry: float | None = None
    stop_loss: float | None = None
    take_profit: tuple[float, ...] = ()


class ScenarioEngine:
    """Builds explicit conditional scenarios from supplied decision evidence."""

    def build(
        self,
        *,
        bullish_probability: float,
        bearish_probability: float,
        neutral_probability: float,
        bullish_condition: str,
        bearish_condition: str,
        neutral_condition: str,
        bullish_invalidation: str,
        bearish_invalidation: str,
        neutral_invalidation: str,
    ) -> tuple[Scenario, ...]:
        values = (
            max(0.0, bullish_probability),
            max(0.0, bearish_probability),
            max(0.0, neutral_probability),
        )
        total = sum(values)
        if total <= 0.0:
            values = (0.0, 0.0, 1.0)
            total = 1.0
        normalized = tuple(value / total for value in values)
        return (
            Scenario(ScenarioDirection.BULLISH, normalized[0], bullish_condition, bullish_invalidation),
            Scenario(ScenarioDirection.BEARISH, normalized[1], bearish_condition, bearish_invalidation),
            Scenario(ScenarioDirection.NEUTRAL, normalized[2], neutral_condition, neutral_invalidation),
        )
