from __future__ import annotations

from dataclasses import dataclass

from analysis.contracts import AnalysisContext, AnalysisOutput
from analysis.multi_timeframe_v2 import MultiTimeframePlanner
from analysis.plugin_runtime_v3 import AnalysisPluginRuntime
from analysis.regime_policy_v2 import MarketRegime, RegimePolicy, RegimePolicyBook
from analysis.registry import AnalyzerRegistry
from analysis.runtime_pipeline_v2 import IntelligenceRuntimeV2
from analysis.selection import AnalysisMode, AnalysisSelection


@dataclass
class StubAnalyzer:
    name: str
    def analyze(self, context: AnalysisContext) -> AnalysisOutput:
        return AnalysisOutput(analyzer=self.name, success=True, values={"source": "stub"})


def runtime() -> IntelligenceRuntimeV2:
    registry = AnalyzerRegistry()
    registry.register("technical", lambda: StubAnalyzer("technical"))
    registry.register("smc", lambda: StubAnalyzer("smc"))
    registry.register("wyckoff", lambda: StubAnalyzer("wyckoff"))
    return IntelligenceRuntimeV2(
        AnalysisPluginRuntime(registry),
        RegimePolicyBook((RegimePolicy(MarketRegime.TREND, ("technical", "smc")),)),
    )


def test_manual_mode_never_injects_unselected_style() -> None:
    plan, result = runtime().run(
        AnalysisContext("TEST", "1h", None),
        AnalysisSelection(AnalysisMode.MANUAL, ("technical",)),
        MarketRegime.TREND,
    )
    assert plan.effective_styles == ("technical",)
    assert result.executed == ("technical",)


def test_smart_mode_uses_regime_policy() -> None:
    plan, result = runtime().run(
        AnalysisContext("TEST", "1h", None),
        AnalysisSelection(AnalysisMode.SMART),
        MarketRegime.TREND,
    )
    assert plan.effective_styles == ("technical", "smc")
    assert result.executed == ("technical", "smc")


def test_plugin_failure_isolated() -> None:
    registry = AnalyzerRegistry()
    registry.register("bad", lambda: StubAnalyzer("bad"))
    result = AnalysisPluginRuntime(registry).run(
        AnalysisContext("TEST", "1h", None),
        AnalysisSelection(AnalysisMode.MANUAL, ("bad",)),
    )
    assert result.executed == ("bad",)
    assert result.results[0].success is True


def test_multi_timeframe_plan_assigns_roles() -> None:
    plan = MultiTimeframePlanner().build(("4h", "1h", "15m"))
    assert plan.roles[0].role == "context"
    assert plan.roles[1].role == "structure"
    assert plan.roles[2].role == "entry"


def test_multi_timeframe_alignment() -> None:
    planner = MultiTimeframePlanner()
    assert planner.alignment({"4h": "bullish", "1h": "bullish"}) == "ALIGNED"
    assert planner.alignment({"4h": "bullish", "1h": "bearish"}) == "CONFLICT"
