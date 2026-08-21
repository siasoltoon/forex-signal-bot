from __future__ import annotations

from datetime import datetime, timezone

import pytest

from data.models import Candle
from data.providers.oanda_provider import OandaProvider
from data.providers.finnhub_provider import FinnhubProvider
from data.providers.alphavantage_provider import AlphaVantageProvider


def test_oanda_provider_name() -> None:
    provider = OandaProvider()

    assert provider.name == "oanda"


def test_finnhub_provider_name() -> None:
    provider = FinnhubProvider()

    assert provider.name == "finnhub"


def test_alphavantage_provider_name() -> None:
    provider = AlphaVantageProvider()

    assert provider.name == "alphavantage"


@pytest.mark.asyncio
async def test_oanda_provider_converts_candles(
    monkeypatch,
) -> None:

    provider = OandaProvider()

    async def fake_get_candles(
        instrument: str,
        granularity: str,
        count: int,
    ):
        return {
            "candles": [
                {
                    "complete": True,
                    "time": "2026-01-01T12:00:00Z",
                    "mid": {
                        "o": "1.1000",
                        "h": "1.1200",
                        "l": "1.0900",
                        "c": "1.1100",
                    },
                    "volume": 100,
                }
            ]
        }

    monkeypatch.setattr(
        provider.client,
        "get_candles",
        fake_get_candles,
    )

    candles = await provider.get_candles(
        symbol="EUR_USD",
        timeframe="M15",
        limit=10,
    )

    assert len(candles) == 1

    candle = candles[0]

    assert isinstance(
        candle,
        Candle,
    )

    assert candle.symbol == "EUR_USD"
    assert candle.close == 1.1100


@pytest.mark.asyncio
async def test_oanda_provider_skips_incomplete_candles(
    monkeypatch,
) -> None:

    provider = OandaProvider()

    async def fake_get_candles(
        instrument: str,
        granularity: str,
        count: int,
    ):
        return {
            "candles": [
                {
                    "complete": False,
                    "time": "2026-01-01T12:00:00Z",
                    "mid": {
                        "o": "1",
                        "h": "1",
                        "l": "1",
                        "c": "1",
                    },
                }
            ]
        }

    monkeypatch.setattr(
        provider.client,
        "get_candles",
        fake_get_candles,
    )

    candles = await provider.get_candles(
        symbol="EUR_USD",
        timeframe="M15",
    )

    assert candles == []


@pytest.mark.asyncio
async def test_finnhub_provider_converts_response(
    monkeypatch,
) -> None:

    provider = FinnhubProvider()

    async def fake_get_candles(
        symbol: str,
        resolution: str,
        from_timestamp: int,
        to_timestamp: int,
    ):

        return {
            "s": "ok",
            "t": [
                1767268800,
            ],
            "o": [
                1.10,
            ],
            "h": [
                1.12,
            ],
            "l": [
                1.09,
            ],
            "c": [
                1.11,
            ],
            "v": [
                100,
            ],
        }

    monkeypatch.setattr(
        provider.client,
        "get_candles",
        fake_get_candles,
    )

    candles = await provider.get_candles(
        symbol="EUR_USD",
        timeframe="M15",
        limit=10,
    )

    assert len(candles) == 1
    assert candles[0].close == 1.11


@pytest.mark.asyncio
async def test_alphavantage_provider_converts_response(
    monkeypatch,
) -> None:

    provider = AlphaVantageProvider()

    async def fake_get_intraday(
        symbol: str,
        interval: str,
    ):

        return {
            "Time Series (15min)": {
                "2026-01-01 12:00:00": {
                    "1. open": "1.1000",
                    "2. high": "1.1200",
                    "3. low": "1.0900",
                    "4. close": "1.1100",
                    "5. volume": "100",
                }
            }
        }

    monkeypatch.setattr(
        provider.client,
        "get_intraday",
        fake_get_intraday,
    )

    candles = await provider.get_candles(
        symbol="EUR_USD",
        timeframe="M15",
        limit=10,
    )

    assert len(candles) == 1

    assert candles[0].close == 1.11


@pytest.mark.asyncio
async def test_provider_invalid_symbol() -> None:

    provider = OandaProvider()

    with pytest.raises(
        ValueError
    ):
        await provider.get_candles(
            symbol="",
            timeframe="M15",
        )
