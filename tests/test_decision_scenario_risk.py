from decision.contracts import DecisionAction, DecisionEvidence
from decision.engine import DecisionEngine
from risk.policy import RiskGate, RiskPolicy
from scenario.contracts import ScenarioType
from scenario.engine import ScenarioEngine


def test_strong_consensus_is_tradable() -> None:
    result = DecisionEngine().evaluate(
        [DecisionEvidence("structure", "BUY", 1.0), DecisionEvidence("momentum", "BUY", 0.8)],
        data_quality=1.0,
        minimum_confidence=0.1,
    )
    assert result.action is DecisionAction.BUY
    assert result.tradable


def test_disagreement_blocks_trade() -> None:
    result = DecisionEngine().evaluate(
        [DecisionEvidence("a", "BUY", 1.0), DecisionEvidence("b", "SELL", 1.0)],
        minimum_confidence=0.1,
        maximum_disagreement=0.2,
    )
    assert result.action is DecisionAction.NO_TRADE
    assert "high_model_disagreement" in result.blockers


def test_scenarios_are_explicit() -> None:
    result = DecisionEngine().evaluate([DecisionEvidence("a", "BUY", 1.0)], minimum_confidence=0.1)
    scenarios = ScenarioEngine().build(result)
    assert len(scenarios) == 3
    assert scenarios[0].kind is ScenarioType.BULLISH


def test_risk_gate_blocks_exposure() -> None:
    gate = RiskGate(RiskPolicy(max_risk_percent=1.0, max_portfolio_exposure_percent=2.0))
    result = gate.evaluate(requested_risk_percent=1.0, open_trades=0, exposure_percent=2.0)
    assert not result.allowed
    assert "max_portfolio_exposure" in result.blockers
