from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pandas as pd
import pytest

from core.errors import ApplicationError
from data.market_data import MarketDataEngine
from data.models import Candle


@pytest.fixture
def candles() -> list[Candle]:
    return [
        Candle(
            symbol="EURUSD",
            timestamp=datetime(2026, 1, 1, 0, 1, tzinfo=timezone.utc),
            open=1.1000,
            high=1.1010,
            low=1.0990,
            close=1.1005,
            volume=100.0,
        ),
        Candle(
            symbol="EURUSD",
            timestamp=datetime(2026, 1, 1, 0, 2, tzinfo=timezone.utc),
            open=1.1005,
            high=1.1020,
            low=1.1000,
            close=1.1015,
            volume=110.0,
        ),
    ]


@pytest.fixture
def manager() -> AsyncMock:
    return AsyncMock()


@pytest.mark.asyncio
async def test_get_candles_normalizes_request_and_returns_dataframe(manager, candles):
    manager.get_candles.return_value = candles
    engine = MarketDataEngine(provider_manager=manager)

    result = await engine.get_candles(" eurusd ", " 15m ", limit=2)

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ["open", "high", "low", "close", "volume"]
    assert isinstance(result.index, pd.DatetimeIndex)
    assert str(result.index.tz) == "UTC"
    assert len(result) == 2
    manager.get_candles.assert_awaited_once_with(
        symbol="EURUSD",
        timeframe="15M",
        limit=2,
    )


@pytest.mark.asyncio
async def test_get_candles_list_returns_quality_gated_candles(manager, candles):
    manager.get_candles.return_value = candles
    engine = MarketDataEngine(provider_manager=manager)

    result = await engine.get_candles_list("EURUSD", "15m", limit=2)

    assert result == candles
    assert all(isinstance(candle, Candle) for candle in result)


@pytest.mark.asyncio
async def test_get_candles_rejects_invalid_request_without_manager_call(manager):
    engine = MarketDataEngine(provider_manager=manager)

    with pytest.raises((TypeError, ValueError)):
        await engine.get_candles("", "15m", limit=10)

    with pytest.raises((TypeError, ValueError)):
        await engine.get_candles("EURUSD", "", limit=10)

    with pytest.raises((TypeError, ValueError)):
        await engine.get_candles("EURUSD", "15m", limit=0)

    manager.get_candles.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_candles_propagates_provider_manager_error(manager):
    manager.get_candles.side_effect = ApplicationError(
        "All market data providers failed.",
        {"provider": "provider_manager", "symbol": "EURUSD"},
    )
    engine = MarketDataEngine(provider_manager=manager)

    with pytest.raises(ApplicationError):
        await engine.get_candles("EURUSD", "15m", limit=10)


@pytest.mark.asyncio
async def test_get_candles_rejects_wrong_candle_collection(manager):
    manager.get_candles.return_value = ["not-a-candle"]
    engine = MarketDataEngine(provider_manager=manager)

    with pytest.raises((TypeError, ValueError)):
        await engine.get_candles("EURUSD", "15m", limit=10)


@pytest.mark.asyncio
async def test_get_candles_returns_empty_normalized_dataframe(manager):
    manager.get_candles.return_value = []
    engine = MarketDataEngine(provider_manager=manager)

    with pytest.raises((TypeError, ValueError)):
        await engine.get_candles("EURUSD", "15m", limit=10)


@pytest.mark.asyncio
async def test_finnhub_compatibility_adapter_filters_timestamp_range(manager, candles):
    manager.get_candles.return_value = candles
    engine = MarketDataEngine(provider_manager=manager)

    result = await engine.get_finnhub_candles(
        "EURUSD",
        "15m",
        int(datetime(2026, 1, 1, 0, 2, tzinfo=timezone.utc).timestamp()),
        int(datetime(2026, 1, 1, 0, 2, tzinfo=timezone.utc).timestamp()),
    )

    assert len(result) == 1
    assert result.index[0] == pd.Timestamp("2026-01-01T00:02:00Z")


@pytest.mark.asyncio
async def test_oanda_compatibility_adapter_delegates_to_unified_contract(manager, candles):
    manager.get_candles.return_value = candles
    engine = MarketDataEngine(provider_manager=manager)

    result = await engine.get_oanda_candles(" eur_usd ", "M15", count=2)

    assert len(result) == 2
    manager.get_candles.assert_awaited_once_with(
        symbol="EUR_USD",
        timeframe="M15",
        limit=2,
    )


@pytest.mark.asyncio
async def test_alphavantage_compatibility_adapter_maps_interval(manager, candles):
    manager.get_candles.return_value = candles
    engine = MarketDataEngine(provider_manager=manager)

    result = await engine.get_alphavantage_intraday("EURUSD", "15min")

    assert len(result) == 2
    manager.get_candles.assert_awaited_once_with(
        symbol="EURUSD",
        timeframe="M15",
        limit=500,
    )


@pytest.mark.asyncio
async def test_alphavantage_adapter_rejects_unknown_interval(manager):
    engine = MarketDataEngine(provider_manager=manager)

    with pytest.raises(ValueError):
        await engine.get_alphavantage_intraday("EURUSD", "2min")

    manager.get_candles.assert_not_awaited()
