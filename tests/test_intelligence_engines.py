from datetime import datetime, timedelta, timezone

from engines.backtest import BacktestCostModel, BacktestExecutionModel
from engines.indicators import IndicatorEngine
from engines.live_monitor import LiveSignalMonitor, LiveSignalState
from engines.market_data import Candle, DataQuality, MarketDataValidator
from engines.portfolio import PortfolioRiskEngine, PositionExposure
from engines.price_action import Direction, PriceActionEngine
from engines.risk import RiskEngine, RiskRequest
from engines.strategy import StrategyDefinition, StrategyEngine


def candles(count: int = 60) -> tuple[Candle, ...]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return tuple(
        Candle(start + timedelta(minutes=i), 100 + i, 101 + i, 99 + i, 100.5 + i)
        for i in range(count)
    )


def test_market_data_validator_accepts_clean_series() -> None:
    report = MarketDataValidator().validate(candles(), expected_seconds=60, stale_after_seconds=10**9)
    assert report.valid
    assert report.quality == DataQuality.EXCELLENT
    assert report.duplicate_count == 0
    assert report.gap_count == 0


def test_indicator_engine_produces_core_indicators() -> None:
    result = IndicatorEngine().compute(candles())
    assert result.sma_fast is not None
    assert result.sma_slow is not None
    assert result.ema_fast is not None
    assert result.rsi is not None
    assert result.atr is not None


def test_price_action_detects_bullish_structure() -> None:
    result = PriceActionEngine().analyze(candles())
    assert result.direction == Direction.BULLISH
    assert result.higher_high


def test_risk_engine_sizes_position_and_enforces_limits() -> None:
    result = RiskEngine().calculate(RiskRequest(10000, 100, 98, 1.0))
    assert result.allowed
    assert result.position_size > 0
    blocked = RiskEngine().calculate(RiskRequest(10000, 100, 98, 2.0))
    assert not blocked.allowed


def test_strategy_engine_ranks_and_retires() -> None:
    engine = StrategyEngine((
        StrategyDefinition("a", "A", (), (), (), historical_expectancy=0.8, stability=0.8),
        StrategyDefinition("b", "B", (), (), (), historical_expectancy=0.2, stability=0.3),
    ))
    assert engine.rank()[0].key == "a"
    engine.retire("a")
    assert all(item.key != "a" for item in engine.rank())


def test_backtest_includes_execution_costs() -> None:
    result = BacktestExecutionModel(BacktestCostModel(spread=0.2, commission_per_unit=0.01, slippage=0.05)).execute(
        side="BUY", entry=100, exit=101, quantity=10
    )
    assert result.net_pnl < result.gross_pnl


def test_portfolio_risk_blocks_excess_concentration() -> None:
    result = PortfolioRiskEngine().evaluate((PositionExposure("EURUSD", 9000, 100), PositionExposure("GBPUSD", 1000, 50)), 10000)
    assert not result.allowed


def test_live_monitor_emits_invalidation_and_confidence_events() -> None:
    now = datetime.now(timezone.utc)
    state = LiveSignalState("sig-1", 0.9, 0.9, now, now)
    updated, events = LiveSignalMonitor().update(state, now=now + timedelta(minutes=1), current_confidence=0.6, invalidated=True)
    assert updated.invalidated
    assert {event.event for event in events} >= {"INVALIDATED", "CONFIDENCE_DROP"}
