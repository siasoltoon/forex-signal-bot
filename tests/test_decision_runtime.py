from analysis.contracts import AnalysisContext, AnalysisOutput
from decision.contracts import AnalysisEvidence, DecisionAction
from decision.engine import DecisionEngine
from decision.scenarios import ScenarioEngine


def test_conflicting_evidence_reduces_confidence_and_can_block_trade() -> None:
    engine = DecisionEngine()
    result = engine.decide((
        AnalysisEvidence("a", "BULLISH", 1, 1, 1, 1),
        AnalysisEvidence("b", "BEARISH", 1, 1, 1, 1),
    ))
    assert result.action is DecisionAction.NO_TRADE
    assert result.disagreement == 1.0


def test_low_data_quality_forces_no_trade() -> None:
    result = DecisionEngine().decide((AnalysisEvidence("a", "BULLISH", 1, 1, 1, 1),), data_quality=0.2)
    assert result.action is DecisionAction.NO_TRADE


def test_weighted_evidence_can_produce_buy() -> None:
    result = DecisionEngine().decide((
        AnalysisEvidence("strong", "BULLISH", 1, 1, 1, 2),
        AnalysisEvidence("weak", "BEARISH", 0.2, 1, 1, 0.25),
    ))
    assert result.action is DecisionAction.BUY


def test_scenarios_are_normalized() -> None:
    scenarios = ScenarioEngine().build(bullish_probability=2, bearish_probability=1, neutral_probability=1)
    assert abs(sum(item.probability for item in scenarios) - 1.0) < 1e-9


def test_analysis_output_can_be_used_without_market_data_access() -> None:
    context = AnalysisContext("TEST", "1H", data=())
    output = AnalysisOutput("fixture", True, {"direction": "BULLISH", "strength": 1.0, "quality": 1.0, "weight": 1.0}, confidence=0.9)
    assert context.symbol == "TEST"
    assert output.success is True
