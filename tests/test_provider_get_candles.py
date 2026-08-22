from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from data.models import Candle
from data.providers.alphavantage_provider import AlphaVantageProvider
from data.providers.finnhub_provider import FinnhubProvider
from data.providers.oanda_provider import OandaProvider


@pytest.fixture
def expected_candles() -> list[Candle]:
    return [
        Candle(
            symbol="EURUSD",
            timestamp="2026-01-01T00:01:00+00:00",
            open=1.1000,
            high=1.1010,
            low=1.0990,
            close=1.1005,
            volume=100.0,
        ),
        Candle(
            symbol="EURUSD",
            timestamp="2026-01-01T00:02:00+00:00",
            open=1.1005,
            high=1.1020,
            low=1.1000,
            close=1.1015,
            volume=110.0,
        ),
    ]


def oanda_response() -> dict:
    return {
        "candles": [
            {
                "complete": True,
                "time": "2026-01-01T00:01:00Z",
                "mid": {"o": "1.1000", "h": "1.1010", "l": "1.0990", "c": "1.1005"},
                "volume": 100,
            },
            {
                "complete": True,
                "time": "2026-01-01T00:02:00Z",
                "mid": {"o": "1.1005", "h": "1.1020", "l": "1.1000", "c": "1.1015"},
                "volume": 110,
            },
        ]
    }


def finnhub_response() -> dict:
    return {
        "s": "ok",
        "t": [1767225660, 1767225720],
        "o": [1.1000, 1.1005],
        "h": [1.1010, 1.1020],
        "l": [1.0990, 1.1000],
        "c": [1.1005, 1.1015],
        "v": [100, 110],
    }


def alphavantage_response() -> dict:
    return {
        "Time Series FX (15min)": {
            "2026-01-01 00:02:00": {
                "1. open": "1.1005",
                "2. high": "1.1020",
                "3. low": "1.1000",
                "4. close": "1.1015",
                "5. volume": "110",
            },
            "2026-01-01 00:01:00": {
                "1. open": "1.1000",
                "2. high": "1.1010",
                "3. low": "1.0990",
                "4. close": "1.1005",
                "5. volume": "100",
            },
        }
    }


@pytest.mark.parametrize(
    "provider_cls,response_factory,client_method",
    [
        (OandaProvider, oanda_response, "get_candles"),
        (FinnhubProvider, finnhub_response, "get_candles"),
        (AlphaVantageProvider, alphavantage_response, "get_intraday"),
    ],
    ids=["oanda", "finnhub", "alphavantage"],
)
@pytest.mark.asyncio
async def test_get_candles_returns_quality_gated_candles(
    provider_cls, response_factory, client_method, expected_candles
):
    client = AsyncMock()
    getattr(client, client_method).return_value = response_factory()
    provider = provider_cls(client=client)

    result = await provider.get_candles("EURUSD", "15m", limit=2)

    assert isinstance(result, list)
    assert all(isinstance(candle, Candle) for candle in result)
    assert len(result) == 2
    assert [candle.symbol.replace("_", "") for candle in result] == [
        "EURUSD",
        "EURUSD",
    ]
    assert [candle.timestamp.isoformat() for candle in result] == [
        candle.timestamp.isoformat() for candle in expected_candles
    ]

    getattr(client, client_method).assert_awaited_once()


@pytest.mark.parametrize(
    "provider_cls,response_factory,client_method",
    [
        (OandaProvider, oanda_response, "get_candles"),
        (FinnhubProvider, finnhub_response, "get_candles"),
        (AlphaVantageProvider, alphavantage_response, "get_intraday"),
    ],
    ids=["oanda", "finnhub", "alphavantage"],
)
@pytest.mark.asyncio
async def test_get_candles_applies_limit(
    provider_cls, response_factory, client_method, expected_candles
):
    client = AsyncMock()
    getattr(client, client_method).return_value = response_factory()
    provider = provider_cls(client=client)

    result = await provider.get_candles("EURUSD", "15m", limit=1)

    assert len(result) == 1
    assert result[0].timestamp.isoformat() == expected_candles[-1].timestamp.isoformat()


@pytest.mark.parametrize(
    "provider_cls,client_method",
    [
        (OandaProvider, "get_candles"),
        (FinnhubProvider, "get_candles"),
        (AlphaVantageProvider, "get_intraday"),
    ],
    ids=["oanda", "finnhub", "alphavantage"],
)
@pytest.mark.asyncio
async def test_get_candles_rejects_invalid_request(provider_cls, client_method):
    client = AsyncMock()
    provider = provider_cls(client=client)

    with pytest.raises((TypeError, ValueError)):
        await provider.get_candles("", "15m", limit=10)

    getattr(client, client_method).assert_not_awaited()
