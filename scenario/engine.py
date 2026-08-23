from __future__ import annotations

from decision.contracts import DecisionAction, DecisionResult
from scenario.contracts import Scenario, ScenarioType


class ScenarioEngine:
    """Creates explicit alternative scenarios without pretending to know the future."""

    def build(self, decision: DecisionResult) -> tuple[Scenario, ...]:
        if decision.action is DecisionAction.BUY:
            return (
                Scenario(ScenarioType.BULLISH, decision.confidence, "bullish setup remains valid", "bullish setup invalidated"),
                Scenario(ScenarioType.BEARISH, 1.0 - decision.confidence, "bearish invalidation trigger occurs", "bearish trigger fails"),
                Scenario(ScenarioType.NEUTRAL, min(1.0, decision.disagreement + 0.1), "directional edge disappears", "directional edge returns"),
            )
        if decision.action is DecisionAction.SELL:
            return (
                Scenario(ScenarioType.BEARISH, decision.confidence, "bearish setup remains valid", "bearish setup invalidated"),
                Scenario(ScenarioType.BULLISH, 1.0 - decision.confidence, "bullish invalidation trigger occurs", "bullish trigger fails"),
                Scenario(ScenarioType.NEUTRAL, min(1.0, decision.disagreement + 0.1), "directional edge disappears", "directional edge returns"),
            )
        return (
            Scenario(ScenarioType.NEUTRAL, max(decision.confidence, 0.5), "no directional edge persists", "directional edge appears"),
            Scenario(ScenarioType.BULLISH, 0.25, "bullish confirmation appears", "bullish confirmation fails"),
            Scenario(ScenarioType.BEARISH, 0.25, "bearish confirmation appears", "bearish confirmation fails"),
        )


__all__ = ["ScenarioEngine"]
