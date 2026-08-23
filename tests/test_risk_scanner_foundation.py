from risk.decision_gate import RiskDecisionGate
from risk.portfolio_guard import PortfolioRiskGuard, PositionRisk
from scanner.opportunity import Opportunity, OpportunityRanker


def test_portfolio_guard_blocks_excess_risk() -> None:
    guard = PortfolioRiskGuard(max_total_risk=0.03)
    result = guard.evaluate((PositionRisk("EURUSD", 0.02, 0.2, "BUY"), PositionRisk("GBPUSD", 0.02, 0.2, "BUY")))
    assert result.allowed is False
    assert result.reason == "maximum_portfolio_risk"


def test_risk_gate_converts_portfolio_failure_to_no_trade() -> None:
    portfolio = PortfolioRiskGuard(max_total_risk=0.01).evaluate((PositionRisk("EURUSD", 0.02, 0.1, "BUY"),))
    result = RiskDecisionGate().evaluate(requested_decision="BUY", portfolio=portfolio)
    assert result.decision == "NO_TRADE"
    assert result.allowed is False


def test_ranker_prefers_quality_and_confidence() -> None:
    ranker = OpportunityRanker()
    items = (
        Opportunity("LOW", "BUY", 90, 0.5, data_quality=0.5),
        Opportunity("HIGH", "BUY", 80, 0.95, data_quality=1.0),
    )
    assert ranker.rank(items)[0].symbol == "HIGH"
