from engines.opportunity_ranker import Opportunity, OpportunityRanker
from engines.portfolio_exposure import PortfolioExposureEngine
from engines.scenario_risk import ScenarioRiskEngine
from engines.signal_lifecycle import SignalLifecycleEngine, SignalState
from engines.strategy_selector import StrategyCandidate, StrategySelector
from engines.stress_test import StressTestEngine


def test_strategy_selector():
    items = [StrategyCandidate("range", "BULLISH", .4, "RANGE"), StrategyCandidate("trend", "BULLISH", .8, "TREND")]
    assert StrategySelector().best(items, "TREND").name == "trend"


def test_scenario_risk():
    plan = ScenarioRiskEngine().build(100, 95, 110, 10000, .01)
    assert plan.risk_reward == 2
    assert ScenarioRiskEngine().approve(plan)


def test_signal_lifecycle():
    result = SignalLifecycleEngine().evaluate("BULLISH", "BULLISH", .9, .5)
    assert result.state == SignalState.WEAKENING


def test_opportunity_ranker():
    items = [Opportunity("A", .8, .7, .2, "BUY"), Opportunity("B", .9, .6, .3, "BUY")]
    assert OpportunityRanker().top(items, 1)[0].symbol == "B"


def test_portfolio_exposure():
    result = PortfolioExposureEngine().assess({"A": 6, "B": -2}, 10, 10, .8)
    assert result.gross == 8
    assert result.blocked is False


def test_stress_test():
    result = StressTestEngine().run([100, 50], [.1, .2], 25)
    assert result.breached is False
