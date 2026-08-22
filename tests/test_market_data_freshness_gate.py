from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from data.market_data import MarketDataEngine
from data.models import Candle
from data.provider_manager import ProviderManager


NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def candle(minutes_ago: int = 10, *, symbol: str = "EURUSD") -> Candle:
    timestamp = NOW - timedelta(minutes=minutes_ago)
    return Candle(
        symbol=symbol,
        timestamp=timestamp,
        open=1.1000,
        high=1.1010,
        low=1.0990,
        close=1.1005,
        volume=100.0,
    )


def engine_with(candles: list[Candle]) -> tuple[MarketDataEngine, AsyncMock]:
    manager = ProviderManager()
    manager.get_candles = AsyncMock(return_value=candles)
    engine = MarketDataEngine(
        provider_manager=manager,
        clock=lambda: NOW,
    )
    return engine, manager.get_candles


@pytest.mark.asyncio
async def test_fresh_data_passes_quality_and_freshness_gates():
    engine, get_candles = engine_with([candle(10)])

    result = await engine.get_candles("EURUSD", "15m", limit=1)

    assert len(result) == 1
    assert result.index.tz is not None
    get_candles.assert_awaited_once_with(
        symbol="EURUSD",
        timeframe="M15",
        limit=1,
    )


@pytest.mark.asyncio
async def test_warning_data_remains_usable():
    engine, _ = engine_with([candle(35)])

    result = await engine.get_candles("EURUSD", "15m", limit=1)

    assert len(result) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("minutes_ago", [46, 90])
async def test_stale_data_is_rejected_before_dataframe_conversion(minutes_ago: int):
    engine, _ = engine_with([candle(minutes_ago)])

    with pytest.raises(ValueError, match="status=STALE"):
        await engine.get_candles("EURUSD", "15m", limit=1)


@pytest.mark.asyncio
async def test_rejected_data_is_rejected_before_dataframe_conversion():
    engine, _ = engine_with([candle(91)])

    with pytest.raises(ValueError, match="status=REJECT"):
        await engine.get_candles("EURUSD", "15m", limit=1)


@pytest.mark.asyncio
async def test_quality_failure_happens_before_freshness_gate():
    engine, _ = engine_with([candle(10, symbol="GBPUSD")])

    with pytest.raises(ValueError, match="unexpected symbol"):
        await engine.get_candles("EURUSD", "15m", limit=1)


@pytest.mark.asyncio
async def test_freshness_is_applied_to_get_candles_list():
    engine, _ = engine_with([candle(46)])

    with pytest.raises(ValueError, match="status=STALE"):
        await engine.get_candles_list("EURUSD", "15m", limit=1)


@pytest.mark.asyncio
async def test_empty_provider_result_remains_empty_and_does_not_require_freshness():
    engine, _ = engine_with([])

    result = await engine.get_candles("EURUSD", "15m", limit=1)

    assert result.empty
    assert str(result.index.tz) == "UTC"


@pytest.mark.asyncio
async def test_invalid_clock_output_is_rejected():
    manager = ProviderManager()
    manager.get_candles = AsyncMock(return_value=[candle(10)])
    engine = MarketDataEngine(
        provider_manager=manager,
        clock=lambda: "2026-01-01T12:00:00+00:00",
    )

    with pytest.raises(TypeError, match="clock must return a datetime"):
        await engine.get_candles("EURUSD", "15m", limit=1)


@pytest.mark.parametrize(
    ("timeframe", "expected"),
    [
        ("M1", timedelta(minutes=1)),
        ("M15", timedelta(minutes=15)),
        ("H1", timedelta(hours=1)),
        ("D1", timedelta(days=1)),
        ("W1", timedelta(weeks=1)),
    ],
)
def test_timeframe_to_timedelta(timeframe: str, expected: timedelta):
    assert MarketDataEngine._timeframe_to_timedelta(timeframe) == expected
