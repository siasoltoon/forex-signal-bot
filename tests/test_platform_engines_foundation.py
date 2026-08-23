from datetime import datetime, timezone

import pytest

from engines.backtest_contracts import ExecutionCostModel
from engines.data_contracts import DataQuality, DataStatus
from engines.live_monitoring import SignalDecay
from engines.portfolio_contracts import PortfolioPosition, PortfolioRiskEngine, PortfolioSnapshot
from engines.risk_contracts import PositionSizingRequest, RiskEngine
from engines.strategy_contracts import Strategy, StrategyDNA, StrategyRegistry, StrategyScore


def test_data_quality_rejects_invalid_score() -> None:
    with pytest.raises(ValueError):
        DataQuality(101, DataStatus.VALID)


def test_risk_engine_sizes_position_without_market_data() -> None:
    result = RiskEngine().size(PositionSizingRequest(10_000, 1, 100, 95))
    assert result.quantity > 0
    assert result.cash_risk == 100


def test_strategy_registry_ranks_active_strategies() -> None:
    registry = StrategyRegistry()
    for strategy_id, score in (("a", 80), ("b", 60)):
        registry.register(
            Strategy(
                StrategyDNA(strategy_id, "forex", ("1H",), "trend", (), (), ()),
                score=StrategyScore(score, score, score, score),
            )
        )
    assert [s.dna.strategy_id for s in registry.ranked()] == ["a", "b"]


def test_portfolio_limits_can_block() -> None:
    snapshot = PortfolioSnapshot(10_000, (PortfolioPosition("X", "forex", 3_000, 500, "LONG"),))
    result = PortfolioRiskEngine().evaluate(snapshot, max_exposure_pct=20, max_risk_pct=10)
    assert result.blocked


def test_signal_decay_is_monotonic() -> None:
    decay = SignalDecay(100)
    assert decay.factor(0) == 1
    assert decay.factor(100) == pytest.approx(0.5)
    assert decay.factor(200) < decay.factor(100)


def test_cost_model_is_additive() -> None:
    assert ExecutionCostModel(2, 3, 4).total_bps() == 9
