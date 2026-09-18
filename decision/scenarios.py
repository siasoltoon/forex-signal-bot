from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ScenarioType(StrEnum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


@dataclass(frozen=True, slots=True)
class Scenario:
    type: ScenarioType
    probability: float
    activation_condition: str
    invalidation_condition: str
    stop_loss: float | None = None
    take_profits: tuple[float, ...] = ()


class ScenarioEngine:
    def build(self, *, bullish_probability: float, bearish_probability: float, neutral_probability: float, bullish_condition: str = "bullish_conditions_confirm", bearish_condition: str = "bearish_conditions_confirm") -> tuple[Scenario, ...]:
        values = (bullish_probability, bearish_probability, neutral_probability)
        if any(value < 0 for value in values):
            raise ValueError("scenario probability mass must be non-negative")
        total = sum(values)
        if total <= 0:
            raise ValueError("scenario probability mass must be positive")
        normalized = tuple(value / total for value in values)
        return (
            Scenario(ScenarioType.BULLISH, normalized[0], bullish_condition, "bullish_invalidation"),
            Scenario(ScenarioType.BEARISH, normalized[1], bearish_condition, "bearish_invalidation"),
            Scenario(ScenarioType.NEUTRAL, normalized[2], "no_directional_confirmation", "directional_confirmation"),
        )
