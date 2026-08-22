from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from data.models import Candle
from data.providers.alphavantage_provider import AlphaVantageProvider
from data.providers.finnhub_provider import FinnhubProvider
from data.providers.oanda_provider import OandaProvider


PROVIDERS = [
    pytest.param(OandaProvider, id="oanda"),
    pytest.param(FinnhubProvider, id="finnhub"),
    pytest.param(AlphaVantageProvider, id="alphavantage"),
]


def _candle(symbol: str, minute: int, close: float) -> Candle:
    return Candle(
        symbol=symbol,
        timestamp=datetime(2026, 1, 1, 0, minute, tzinfo=timezone.utc),
        open=close - 0.1,
        high=close + 0.2,
        low=close - 0.2,
        close=close,
        volume=100.0,
    )


@pytest.mark.parametrize("provider_cls", PROVIDERS)
def test_provider_contract_exposes_canonical_timeframe(provider_cls):
    assert provider_cls.normalize_timeframe("15m") == "M15"
    assert provider_cls.normalize_timeframe("1h") == "H1"


@pytest.mark.parametrize("provider_cls", PROVIDERS)
def test_provider_contract_rejects_invalid_requests(provider_cls):
    with pytest.raises((TypeError, ValueError)):
        provider_cls.validate_request("EURUSD", "15m", 0)

    with pytest.raises((TypeError, ValueError)):
        provider_cls.validate_request("", "15m", 10)


@pytest.mark.parametrize("provider_cls", PROVIDERS)
def test_provider_contract_normalizes_candles(provider_cls):
    candles = [
        _candle("EURUSD", 2, 1.2),
        _candle("EURUSD", 1, 1.1),
        _candle("EURUSD", 1, 1.15),
    ]

    normalized = provider_cls.normalize_candles(
        candles,
        expected_symbol="EURUSD",
        deduplicate=True,
    )

    assert len(normalized) == 2
    assert [c.timestamp.minute for c in normalized] == [1, 2]
    assert all(c.timestamp.tzinfo is not None for c in normalized)


@pytest.mark.parametrize("provider_cls", PROVIDERS)
def test_provider_contract_applies_limit(provider_cls):
    candles = [
        _candle("EURUSD", 1, 1.1),
        _candle("EURUSD", 2, 1.2),
        _candle("EURUSD", 3, 1.3),
    ]

    limited = provider_cls.apply_limit(candles, 2)

    assert len(limited) == 2
    assert [c.timestamp.minute for c in limited] == [2, 3]


@pytest.mark.parametrize("provider_cls", PROVIDERS)
def test_provider_contract_client_is_injectable(provider_cls):
    client = AsyncMock()
    provider = provider_cls(client=client)
    assert provider.client is client
