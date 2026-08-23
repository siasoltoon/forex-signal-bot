from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from engines.confidence import ConfidenceEngine, ConfidenceResult
from engines.decision_engine import DecisionEngine, DecisionResult
from engines.scenario_engine import ScenarioEngine


@dataclass(frozen=True, slots=True)
class IntelligenceResult:
    decision: DecisionResult
    confidence: ConfidenceResult


class IntelligenceOrchestrator:
    def __init__(self) -> None:
        self._confidence = ConfidenceEngine()
        self._scenarios = ScenarioEngine()
        self._decision = DecisionEngine()

    def run(
        self,
        score: float,
        agreement: float,
        data_quality: float,
        historical_quality: float,
        disagreement: float,
        regime_confidence: float,
        risk_blocked: bool = False,
        event_blocked: bool = False,
    ) -> IntelligenceResult:
        confidence = self._confidence.calculate(
            agreement,
            data_quality,
            historical_quality,
            disagreement,
            regime_confidence,
        )
        scenarios = self._scenarios.build(score)
        decision = self._decision.decide(
            score,
            confidence,
            scenarios,
            risk_blocked=risk_blocked,
            event_blocked=event_blocked,
        )
        return IntelligenceResult(decision, confidence)
