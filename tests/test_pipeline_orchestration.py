from analysis.contracts import AnalysisContext, AnalysisOutput
from analysis.orchestrator import AnalysisOrchestrator
from analysis.registry import AnalyzerRegistry
from application.pipeline import IntelligencePipeline
from strategy.contracts import StrategyContext, StrategyDecision
from strategy.orchestrator import StrategyOrchestrator
from strategy.registry import StrategyRegistry


class GoodAnalyzer:
    name = "good"

    def analyze(self, context: AnalysisContext) -> AnalysisOutput:
        return AnalysisOutput(self.name, True, {"direction": "bullish"})


class BadAnalyzer:
    name = "bad"

    def analyze(self, context: AnalysisContext) -> AnalysisOutput:
        raise RuntimeError("boom")


class GoodStrategy:
    name = "good-strategy"

    def evaluate(self, context: StrategyContext) -> StrategyDecision:
        return StrategyDecision(self.name, "BUY", 0.8, "test")


def test_analysis_orchestrator_isolates_failures() -> None:
    registry = AnalyzerRegistry()
    registry.register("good", GoodAnalyzer)
    registry.register("bad", BadAnalyzer)
    result = AnalysisOrchestrator(registry).run(
        AnalysisContext("EURUSD", "1H", data=[]),
        ["good", "bad"],
    )
    assert len(result.successful) == 1
    assert len(result.failed) == 1


def test_pipeline_composes_analysis_and_strategy() -> None:
    analyzers = AnalyzerRegistry()
    analyzers.register("good", GoodAnalyzer)
    strategies = StrategyRegistry()
    strategies.register("good-strategy", GoodStrategy)

    pipeline = IntelligencePipeline(
        AnalysisOrchestrator(analyzers),
        StrategyOrchestrator(strategies),
    )
    result = pipeline.run(AnalysisContext("EURUSD", "1H", data=[]), analyzers=["good"])
    assert result.analysis.successful
    assert result.decisions[0].action == "BUY"
