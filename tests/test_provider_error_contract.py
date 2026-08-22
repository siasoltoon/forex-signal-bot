from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from core.errors import ApplicationError
from data.providers.alphavantage_provider import AlphaVantageProvider
from data.providers.finnhub_provider import FinnhubProvider
from data.providers.oanda_provider import OandaProvider


PROVIDERS = [
    (OandaProvider, "get_candles", "oanda"),
    (FinnhubProvider, "get_candles", "finnhub"),
    (AlphaVantageProvider, "get_intraday", "alphavantage"),
]


@pytest.mark.parametrize(
    "provider_cls,client_method,provider_name",
    PROVIDERS,
    ids=["oanda", "finnhub", "alphavantage"],
)
@pytest.mark.asyncio
async def test_get_candles_maps_client_exception_to_application_error(
    provider_cls, client_method, provider_name
):
    client = AsyncMock()
    getattr(client, client_method).side_effect = TimeoutError("upstream timeout")
    provider = provider_cls(client=client)

    with pytest.raises(ApplicationError) as exc_info:
        await provider.get_candles("EURUSD", "15m", limit=10)

    error = exc_info.value
    assert error.details["provider"] == provider_name
    assert error.details["symbol"] == (
        "EUR_USD" if provider_name == "oanda" else "EURUSD"
    )
    assert error.details["limit"] == 10
    getattr(client, client_method).assert_awaited_once()


@pytest.mark.parametrize(
    "provider_cls,client_method",
    [(provider_cls, client_method) for provider_cls, client_method, _ in PROVIDERS],
    ids=["oanda", "finnhub", "alphavantage"],
)
@pytest.mark.asyncio
async def test_get_candles_rejects_non_mapping_response(provider_cls, client_method):
    client = AsyncMock()
    getattr(client, client_method).return_value = []
    provider = provider_cls(client=client)

    with pytest.raises(ApplicationError):
        await provider.get_candles("EURUSD", "15m", limit=10)


@pytest.mark.parametrize(
    "provider_cls,client_method",
    [(provider_cls, client_method) for provider_cls, client_method, _ in PROVIDERS],
    ids=["oanda", "finnhub", "alphavantage"],
)
@pytest.mark.asyncio
async def test_get_candles_does_not_call_client_for_invalid_request(
    provider_cls, client_method
):
    client = AsyncMock()
    provider = provider_cls(client=client)

    with pytest.raises((TypeError, ValueError)):
        await provider.get_candles("", "15m", limit=10)

    getattr(client, client_method).assert_not_awaited()
