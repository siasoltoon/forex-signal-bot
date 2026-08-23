from analysis.contracts import AnalysisContext, AnalysisOutput
from analysis.registry import AnalyzerRegistry
from strategy.contracts import StrategyDecision
from strategy.registry import StrategyRegistry
from signal_engine.lifecycle import SignalLifecycle, SignalSnapshot, SignalStatus
from signal_engine.pipeline import SignalPipeline


class StubAnalyzer:
    name = "stub"

    def analyze(self, context):
        return AnalysisOutput(analyzer=self.name, success=True, values={"ok": True})


class StubStrategy:
    name = "stub-strategy"

    def evaluate(self, context):
        return StrategyDecision(
            strategy=self.name,
            action="buy",
            confidence=0.8,
            reason="test",
            metadata={"entry": 100, "stop_loss": 95, "take_profit": 110},
        )


def test_signal_lifecycle_update_and_terminal_guard():
    signal = SignalSnapshot(signal_id="1", symbol="EURUSD", direction="buy", entry=100)
    lifecycle = SignalLifecycle()
    updated = lifecycle.update(signal, confidence=0.9)
    assert updated.status is SignalStatus.UPDATED
    assert updated.version == 2
    closed = lifecycle.transition(updated, SignalStatus.CLOSED)
    assert closed.status is SignalStatus.CLOSED
    try:
        lifecycle.update(closed)
    except ValueError:
        pass
    else:
        raise AssertionError("terminal signal must not be updated")


def test_pipeline_creates_signal_from_strategy_decision():
    analyzers = AnalyzerRegistry()
    analyzers.register("stub", StubAnalyzer)
    strategies = StrategyRegistry()
    strategies.register("stub-strategy", StubStrategy)
    pipeline = SignalPipeline(analyzers, strategies)
    result = pipeline.run(AnalysisContext(symbol="EURUSD", timeframe="M15", data=[]))
    assert len(result.analysis.successful) == 1
    assert len(result.strategies.decisions) == 1
    assert len(result.signals) == 1
    assert result.signals[0].take_profit == 110.0
