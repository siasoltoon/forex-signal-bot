from __future__ import annotations

import pytest

from services.market_data.service import MarketDataService


class FakeManager:

    async def get_candles(
        self,
        provider_name,
        symbol,
        timeframe,
        limit,
    ):
        return [
            "candle"
        ]



@pytest.mark.asyncio
async def test_service_returns_candles():

    service = MarketDataService(
        FakeManager()
    )


    result = await service.get_candles(
        symbol="EUR_USD",
        timeframe="M15",
        limit=10,
    )


    assert result == [
        "candle"
    ]



@pytest.mark.asyncio
async def test_service_invalid_limit():

    service = MarketDataService(
        FakeManager()
    )


    with pytest.raises(
        ValueError
    ):

        await service.get_candles(
            symbol="EUR_USD",
            timeframe="M15",
            limit=0,
        )
