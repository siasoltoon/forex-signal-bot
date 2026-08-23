from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Scenario:
    name: str
    probability: float
    activation: str
    invalidation: str


class ScenarioEngine:
    def normalize(self, scenarios: list[Scenario]) -> tuple[Scenario, ...]:
        if not scenarios:
            return ()
        total = sum(max(0.0, s.probability) for s in scenarios)
        if total <= 0:
            raise ValueError("scenario probabilities must have positive total")
        return tuple(Scenario(s.name, max(0.0, s.probability) / total, s.activation, s.invalidation) for s in scenarios)

    def build(self, score: float) -> tuple[Scenario, ...]:
        bullish = max(0.0, 0.5 + score / 2)
        bearish = max(0.0, 0.5 - score / 2)
        neutral = max(0.0, 1.0 - bullish - bearish)
        return self.normalize([
            Scenario("BULLISH", bullish, "bullish confirmation", "bullish structure invalidated"),
            Scenario("BEARISH", bearish, "bearish confirmation", "bearish structure invalidated"),
            Scenario("NEUTRAL", neutral, "no directional confirmation", "directional breakout"),
        ])
