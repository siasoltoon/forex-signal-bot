from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from analysis.contracts import AnalysisContext, AnalysisRun
from analysis.orchestrator import AnalysisOrchestrator, AnalysisPolicy
from strategy.contracts import StrategyContext, StrategyDecision
from strategy.orchestrator import StrategyOrchestrator, StrategyRun


@dataclass(frozen=True)
class IntelligenceRun:
    analysis: AnalysisRun
    strategies: StrategyRun | None = None

    @property
    def decisions(self) -> tuple[StrategyDecision, ...]:
        if self.strategies is None:
            return ()
        return self.strategies.decisions


class IntelligencePipeline:
    """Application-level composition of validated analysis and strategy stages."""

    def __init__(
        self,
        analysis: AnalysisOrchestrator,
        strategies: StrategyOrchestrator | None = None,
    ) -> None:
        self.analysis = analysis
        self.strategies = strategies

    def run(
        self,
        context: AnalysisContext,
        *,
        analyzers: Iterable[str] | None = None,
        strategies: Iterable[str] | None = None,
        minimum_successful_analyzers: int = 0,
    ) -> IntelligenceRun:
        selected_analyzers = tuple(analyzers) if analyzers is not None else None
        selected_strategies = tuple(strategies) if strategies is not None else None
        analysis_run = self.analysis.run(
            context,
            selected_analyzers,
            policy=AnalysisPolicy(
                analyzers=selected_analyzers or (),
                minimum_successful=minimum_successful_analyzers,
            ),
        )

        if self.strategies is None or not analysis_run.successful:
            return IntelligenceRun(analysis=analysis_run)

        strategy_context = StrategyContext(
            symbol=context.symbol,
            timeframe=context.timeframe,
            analysis=analysis_run,
            metadata=context.metadata,
        )
        return IntelligenceRun(
            analysis=analysis_run,
            strategies=self.strategies.run(strategy_context, selected_strategies),
        )


__all__ = ["IntelligencePipeline", "IntelligenceRun"]
