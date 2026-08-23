from engines.analyzer_registry import AnalyzerRegistry, AnalyzerSpec
from engines.decision_engine import DecisionEngine
from engines.risk_gate import RiskGateEngine
from engines.scenario_engine import ScenarioEngine
from engines.intelligence_orchestrator import IntelligenceOrchestrator


def test_analyzer_registry_filters_disabled():
    registry = AnalyzerRegistry()
    registry.register(AnalyzerSpec("technical", lambda: None))
    registry.register(AnalyzerSpec("volume", lambda: None, enabled=False))
    assert registry.names() == ("technical", "volume")
    assert [x.name for x in registry.active()] == ["technical"]


def test_risk_gate_blocks_excess_exposure():
    result = RiskGateEngine().evaluate(0.01, 0.20)
    assert result.blocked is True
    assert "portfolio exposure limit" in result.reasons


def test_decision_engine_blocks_risk():
    confidence = __import__("engines.confidence", fromlist=["ConfidenceResult"]).ConfidenceResult(0.9, 0.1, False)
    scenarios = ScenarioEngine().build(0.8)
    result = DecisionEngine().decide(0.8, confidence, scenarios, risk_blocked=True)
    assert result.decision == "NO_TRADE"
    assert result.trace[-1]["stage"] == "decision"


def test_orchestrator_produces_no_trade_on_low_quality():
    result = IntelligenceOrchestrator().run(0.8, 0.9, 0.2, 0.9, 0.1, 0.9)
    assert result.decision.decision == "NO_TRADE"
