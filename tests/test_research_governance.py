from backtest.monte_carlo import MonteCarloSimulator
from backtest.stress import StressScenario, StressTester
from evaluation.research import EvaluationRecord, summarize
from model.registry import ModelRecord, ModelRegistry, ModelState
from strategy.retirement import StrategyRetirementPolicy


def test_evaluation_summary_groups_strategies() -> None:
    result = summarize((EvaluationRecord("a", "w1", 1.0, 0.1, 10), EvaluationRecord("a", "w2", 3.0, 0.2, 5)))
    assert result[0].strategy_id == "a"
    assert result[0].average_score == 2.0
    assert result[0].total_trades == 15


def test_strategy_retirement_requires_evidence() -> None:
    decision = StrategyRetirementPolicy(minimum_score=0.5, minimum_trades=10).evaluate("s", score=0.0, drawdown=0.0, trades=2)
    assert decision.retired is False
    assert decision.reason == "insufficient_evidence"


def test_monte_carlo_is_reproducible() -> None:
    simulator = MonteCarloSimulator()
    assert simulator.simulate((1.0, -0.5, 2.0), runs=20, seed=7) == simulator.simulate((1.0, -0.5, 2.0), runs=20, seed=7)


def test_stress_adjusts_supplied_pnl() -> None:
    result = StressTester().run(100.0, StressScenario("high_cost", fee_multiplier=2.0, slippage_multiplier=2.0))
    assert result.adjusted_pnl < 100.0


def test_model_registry_lifecycle() -> None:
    registry = ModelRegistry()
    registry.register(ModelRecord("m", "1", ModelState.CANDIDATE))
    updated = registry.transition("m", ModelState.CHAMPION)
    assert updated.state == ModelState.CHAMPION
