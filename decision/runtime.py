from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from analysis.contracts import AnalysisContext
from analysis.orchestrator import AnalysisOrchestrator
from decision.contracts import AnalysisEvidence, DecisionResult
from decision.engine import DecisionEngine
from decision.scenarios import Scenario, ScenarioEngine


@dataclass(frozen=True, slots=True)
class DecisionRun:
    decision: DecisionResult
    scenarios: tuple[Scenario, ...]


class DecisionRuntime:
    """Coordinates analysis output into a safe decision envelope."""

    def __init__(self, orchestrator: AnalysisOrchestrator, engine: DecisionEngine | None = None, scenarios: ScenarioEngine | None = None) -> None:
        self.orchestrator = orchestrator
        self.engine = engine or DecisionEngine()
        self.scenarios = scenarios or ScenarioEngine()

    def run(self, context: AnalysisContext, analyzers: Iterable[str] | None = None, *, data_quality: float = 1.0, regime_known: bool = True) -> DecisionRun:
        analysis = self.orchestrator.run(context, analyzers)
        evidence: list[AnalysisEvidence] = []
        for result in analysis.successful:
            values = result.values
            evidence.append(
                AnalysisEvidence(
                    name=result.analyzer,
                    direction=str(values.get("direction", "NEUTRAL")),
                    strength=float(values.get("strength", 0.0)),
                    quality=float(values.get("quality", 1.0)),
                    confidence=float(result.confidence or 0.0),
                    weight=float(values.get("weight", 1.0)),
                    timeframe=context.timeframe,
                )
            )
        decision = self.engine.decide(evidence, data_quality=data_quality, regime_known=regime_known)
        bullish = max(0.0, min(1.0, 0.5 + decision.score / 2.0))
        bearish = max(0.0, min(1.0, 0.5 - decision.score / 2.0))
        neutral = max(0.0, 1.0 - max(bullish, bearish))
        scenarios = self.scenarios.build(bullish_probability=bullish, bearish_probability=bearish, neutral_probability=neutral)
        return DecisionRun(decision, scenarios)
