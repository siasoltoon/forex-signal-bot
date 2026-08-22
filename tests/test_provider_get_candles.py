from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from data.models import Candle
from data.providers.alphavantage_provider import AlphaVantageProvider
from data.providers.finnhub_provider import FinnhubProvider
from data.providers.oanda_provider import OandaProvider


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


@pytest.mark.parametrize(
    "provider_cls",
    [OandaProvider, FinnhubProvider, AlphaVantageProvider],
    ids=["oanda", "finnhub", "alphavantage"],
)
@pytest.mark.asyncio
async def test_get_candles_returns_quality_gated_candles(provider_cls, candles):
    client = AsyncMock()
    client.get_candles.return_value = candles
    provider = provider_cls(client=client)

    result = await provider.get_candles("EURUSD", "15m", limit=2)

    assert isinstance(result, list)
    assert all(isinstance(candle, Candle) for candle in result)
    assert len(result) == 2
    assert [candle.timestamp for candle in result] == [
        candles[0].timestamp,
        candles[1].timestamp,
    ]

    client.get_candles.assert_awaited_once()


@pytest.mark.parametrize(
    "provider_cls",
    [OandaProvider, FinnhubProvider, AlphaVantageProvider],
    ids=["oanda", "finnhub", "alphavantage"],
)
@pytest.mark.asyncio
async def test_get_candles_applies_limit(provider_cls, candles):
    client = AsyncMock()
    client.get_candles.return_value = candles
    provider = provider_cls(client=client)

    result = await provider.get_candles("EURUSD", "15m", limit=1)

    assert len(result) == 1
    assert result[0].timestamp == candles[-1].timestamp


@pytest.mark.parametrize(
    "provider_cls",
    [OandaProvider, FinnhubProvider, AlphaVantageProvider],
    ids=["oanda", "finnhub", "alphavantage"],
)
@pytest.mark.asyncio
async def test_get_candles_rejects_invalid_request(provider_cls):
    client = AsyncMock()
    provider = provider_cls(client=client)

    with pytest.raises((TypeError, ValueError)):
        await provider.get_candles("", "15m", limit=10)

    client.get_candles.assert_not_awaited()
