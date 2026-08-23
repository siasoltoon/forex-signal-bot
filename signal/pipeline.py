from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from analysis.contracts import AnalysisContext
from analysis.orchestrator import AnalysisOrchestrator, AnalysisRun
from analysis.registry import AnalyzerRegistry
from strategy.contracts import StrategyContext, StrategyDecision
from strategy.orchestrator import StrategyOrchestrator, StrategyRun
from strategy.registry import StrategyRegistry
from signal.lifecycle import SignalLifecycle, SignalSnapshot


@dataclass(frozen=True)
class PipelineRun:
    analysis: AnalysisRun
    strategies: StrategyRun
    signals: tuple[SignalSnapshot, ...]


class SignalPipeline:
    """Coordinates analysis, strategy evaluation and signal lifecycle creation."""

    def __init__(
        self,
        analyzer_registry: AnalyzerRegistry,
        strategy_registry: StrategyRegistry,
        *,
        analysis_workers: int = 1,
    ) -> None:
        self.analysis = AnalysisOrchestrator(analyzer_registry, max_workers=analysis_workers)
        self.strategies = StrategyOrchestrator(strategy_registry)
        self.lifecycle = SignalLifecycle()

    def run(
        self,
        context: AnalysisContext,
        *,
        analyzers: Iterable[str] | None = None,
        strategies: Iterable[str] | None = None,
    ) -> PipelineRun:
        analysis_run = self.analysis.run(context, analyzers)
        strategy_context = StrategyContext(
            symbol=context.symbol,
            timeframe=context.timeframe,
            analysis=analysis_run,
            metadata=context.metadata,
        )
        strategy_run = self.strategies.run(strategy_context, strategies)
        signals = tuple(
            self._decision_to_signal(decision, context)
            for decision in strategy_run.decisions
            if decision.action.lower() in {"buy", "sell", "long", "short"}
        )
        return PipelineRun(analysis=analysis_run, strategies=strategy_run, signals=signals)

    @staticmethod
    def _decision_to_signal(decision: StrategyDecision, context: AnalysisContext) -> SignalSnapshot:
        metadata = dict(decision.metadata)
        entry = float(metadata.get("entry", context.metadata.get("entry", 0.0)))
        stop_loss = metadata.get("stop_loss", context.metadata.get("stop_loss"))
        take_profit = metadata.get("take_profit", context.metadata.get("take_profit"))
        return SignalSnapshot(
            signal_id=f"{context.symbol}:{context.timeframe}:{decision.strategy}",
            symbol=context.symbol,
            direction=decision.action.lower(),
            entry=entry,
            stop_loss=float(stop_loss) if stop_loss is not None else None,
            take_profit=float(take_profit) if take_profit is not None else None,
            confidence=decision.confidence,
            reason=decision.reason,
            metadata=metadata,
        )
