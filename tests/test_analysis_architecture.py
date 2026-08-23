from analysis.adapters import LegacyAnalysisEngineAdapter, register_legacy_analyzers
from analysis.contracts import AnalysisContext, AnalysisOutput
from analysis.orchestrator import AnalysisOrchestrator
from analysis.registry import AnalyzerRegistry


class StubAnalyzer:
    name = "stub"

    def analyze(self, context: AnalysisContext) -> AnalysisOutput:
        return AnalysisOutput(analyzer=self.name, success=True, values={"symbol": context.symbol})


def test_registry_registers_and_creates_analyzer():
    registry = AnalyzerRegistry()
    registry.register("stub", StubAnalyzer)
    assert registry.names() == ("stub",)
    assert isinstance(registry.create("stub"), StubAnalyzer)


def test_orchestrator_isolates_failures():
    class Broken:
        name = "broken"

        def analyze(self, context):
            raise RuntimeError("boom")

    registry = AnalyzerRegistry()
    registry.register("broken", Broken)
    run = AnalysisOrchestrator(registry).run(AnalysisContext("EURUSD", "H1", []))
    assert len(run.failed) == 1
    assert "RuntimeError" in run.failed[0].error


def test_legacy_engine_can_be_registered_without_rewrite():
    registry = AnalyzerRegistry()
    register_legacy_analyzers(registry)
    analyzer = registry.create("technical")
    assert isinstance(analyzer, LegacyAnalysisEngineAdapter)
