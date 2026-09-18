from evaluation.continuous import ContinuousEvaluator, EvaluationSnapshot
from evaluation.model_lifecycle import ChampionChallenger, ModelScore
from evaluation.rollback import RollbackGuard
from evaluation.walk_forward import WalkForwardPlanner
from strategy.evaluation import StrategyEvaluator, StrategyScore


def test_walk_forward_windows_are_causal() -> None:
    windows = WalkForwardPlanner(3, 2).plan((1, 2, 3, 4, 5, 6, 7))
    assert windows[0].train_end < windows[0].test_start
    assert windows[0].test_end == 5


def test_challenger_requires_improvement() -> None:
    result = ChampionChallenger(minimum_improvement=0.1).evaluate(
        ModelScore("champion", 0.8), ModelScore("challenger", 0.85)
    )
    assert result.promoted is False
    assert result.active_model == "champion"


def test_unhealthy_snapshot_triggers_rollback_path() -> None:
    status = ContinuousEvaluator(minimum_samples=10).evaluate(EvaluationSnapshot("m", 0.8, 0.1, 2))
    decision = RollbackGuard().evaluate(active_model="m", last_known_good="good", healthy=status.healthy)
    assert decision.rollback is True
    assert decision.target_model == "good"


def test_strategy_ranking_prefers_stable_lower_drawdown() -> None:
    ranked = StrategyEvaluator().rank((
        StrategyScore("a", 1.0, 0.5, 0.2, 20),
        StrategyScore("b", 0.9, 1.0, 0.05, 20),
    ))
    assert ranked[0].strategy == "b"
