from __future__ import annotations

import pytest

from core.errors import ApplicationError
from services.market_data.service import MarketDataService


class FakeManager:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    async def get_candles(self, provider_name, symbol, timeframe, limit):
        self.calls.append(
            {
                "provider_name": provider_name,
                "symbol": symbol,
                "timeframe": timeframe,
                "limit": limit,
            }
        )
        if self.error is not None:
            raise self.error
        return self.result


@pytest.mark.asyncio
async def test_service_forwards_normalized_request():
    manager = FakeManager(result=["candle"])
    service = MarketDataService(manager)

    result = await service.get_candles(
        symbol=" eur_usd ",
        timeframe="M15",
        limit=10,
        provider_name=" OANDA ",
    )

    assert result == ["candle"]
    assert manager.calls == [
        {
            "provider_name": " OANDA ",
            "symbol": "EUR_USD",
            "timeframe": "M15",
            "limit": 10,
        }
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "kwargs",
    [
        {"symbol": "", "timeframe": "M15", "limit": 10},
        {"symbol": "EUR_USD", "timeframe": "", "limit": 10},
        {"symbol": "EUR_USD", "timeframe": "M15", "limit": 0},
        {"symbol": "EUR_USD", "timeframe": "M15", "limit": -1},
        {"symbol": "EUR_USD", "timeframe": "M15", "limit": True},
    ],
)
async def test_service_rejects_invalid_request(kwargs):
    service = MarketDataService(FakeManager(result=[]))

    with pytest.raises((TypeError, ValueError, ApplicationError)):
        await service.get_candles(**kwargs)


@pytest.mark.asyncio
async def test_service_rejects_invalid_provider_name():
    service = MarketDataService(FakeManager(result=[]))

    with pytest.raises((TypeError, ValueError)):
        await service.get_candles(
            symbol="EUR_USD",
            timeframe="M15",
            limit=10,
            provider_name="   ",
        )


@pytest.mark.asyncio
async def test_service_propagates_application_error():
    manager = FakeManager(error=ApplicationError("upstream failure"))
    service = MarketDataService(manager)

    with pytest.raises(ApplicationError):
        await service.get_candles(
            symbol="EUR_USD",
            timeframe="M15",
            limit=10,
        )


@pytest.mark.asyncio
async def test_service_wraps_unexpected_manager_error():
    manager = FakeManager(error=RuntimeError("network failure"))
    service = MarketDataService(manager)

    with pytest.raises(ApplicationError):
        await service.get_candles(
            symbol="EUR_USD",
            timeframe="M15",
            limit=10,
        )


@pytest.mark.asyncio
async def test_service_returns_empty_list_for_none_result():
    service = MarketDataService(FakeManager(result=None))

    result = await service.get_candles(
        symbol="EUR_USD",
        timeframe="M15",
        limit=10,
    )

    assert result == []


@pytest.mark.asyncio
@pytest.mark.parametrize("result", ["invalid", {"candle": 1}])
async def test_service_rejects_non_list_manager_result(result):
    service = MarketDataService(FakeManager(result=result))

    with pytest.raises(ApplicationError):
        await service.get_candles(
            symbol="EUR_USD",
            timeframe="M15",
            limit=10,
        )
