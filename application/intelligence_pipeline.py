from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from analysis.contracts import AnalysisContext, AnalysisRun
from analysis.orchestrator import AnalysisOrchestrator


class DataGate(Protocol):
    def validate(self, *, symbol: str, timeframe: str, data: Any) -> Any: ...


class StrategyRunner(Protocol):
    def run(self, analysis: AnalysisRun) -> Any: ...


class DecisionRunner(Protocol):
    def evaluate(self, analysis: AnalysisRun, strategies: Any) -> Any: ...


class RiskRunner(Protocol):
    def evaluate(self, decision: Any) -> Any: ...


@dataclass(frozen=True, slots=True)
class PipelineResult:
    context: AnalysisContext
    analysis: AnalysisRun | None = None
    strategies: Any = None
    decision: Any = None
    risk: Any = None
    blocked: bool = False
    blockers: tuple[str, ...] = ()
    trace: tuple[str, ...] = ()


@dataclass(slots=True)
class IntelligencePipeline:
    """Single application boundary for validated-data-to-decision flow.

    Components remain replaceable through protocols. No market data is
    fabricated or inferred by this orchestration layer.
    """

    analysis: AnalysisOrchestrator
    data_gate: DataGate | None = None
    strategy: StrategyRunner | None = None
    decision: DecisionRunner | None = None
    risk: RiskRunner | None = None

    def run(
        self,
        *,
        context: AnalysisContext,
        analyzers: tuple[str, ...] | None = None,
    ) -> PipelineResult:
        trace: list[str] = ["request"]

        if self.data_gate is not None:
            self.data_gate.validate(
                symbol=context.symbol,
                timeframe=context.timeframe,
                data=context.data,
            )
        trace.append("validated_data")

        analysis_run = self.analysis.run(context, analyzers)
        trace.append("analysis")

        if not analysis_run.successful:
            return PipelineResult(
                context=context,
                analysis=analysis_run,
                blocked=True,
                blockers=("no_successful_analysis",),
                trace=tuple(trace + ["no_trade"]),
            )

        strategies = self.strategy.run(analysis_run) if self.strategy is not None else None
        trace.append("strategy") if self.strategy is not None else None

        decision = self.decision.evaluate(analysis_run, strategies) if self.decision is not None else None
        trace.append("decision") if self.decision is not None else None

        risk = self.risk.evaluate(decision) if self.risk is not None and decision is not None else None
        trace.append("risk") if self.risk is not None and decision is not None else None

        blocked = bool(getattr(risk, "allowed", True) is False)
        blockers = tuple(getattr(risk, "blockers", ()))
        if blocked:
            trace.append("no_trade")

        return PipelineResult(
            context=context,
            analysis=analysis_run,
            strategies=strategies,
            decision=decision,
            risk=risk,
            blocked=blocked,
            blockers=blockers,
            trace=tuple(trace),
        )


__all__ = ["DataGate", "DecisionRunner", "IntelligencePipeline", "PipelineResult", "RiskRunner", "StrategyRunner"]
