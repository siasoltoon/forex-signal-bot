from __future__ import annotations

import pytest

from data.fallback import FallbackProvider
from data.base import MarketDataProvider
from data.models import Candle


class FakeProvider(MarketDataProvider):

    def __init__(
        self,
        name: str,
        candles=None,
        error=None,
    ):
        self.name = name
        self.candles = candles or []
        self.error = error


    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ):

        if self.error:
            raise self.error

        return self.candles[:limit]



@pytest.mark.asyncio
async def test_fallback_uses_second_provider():

    first = FakeProvider(
        name="first",
        error=RuntimeError(
            "failed"
        ),
    )


    second = FakeProvider(
        name="second",
        candles=[
            "candle"
        ],
    )


    fallback = FallbackProvider(
        [
            first,
            second,
        ]
    )


    result = await fallback.get_candles(
        symbol="EUR_USD",
        timeframe="M15",
    )


    assert result == [
        "candle"
    ]



@pytest.mark.asyncio
async def test_all_providers_fail():

    fallback = FallbackProvider(
        [
            FakeProvider(
                name="one",
                error=RuntimeError(),
            ),
            FakeProvider(
                name="two",
                error=RuntimeError(),
            ),
        ]
    )


    with pytest.raises(Exception):
        await fallback.get_candles(
            symbol="EUR_USD",
            timeframe="M15",
        )
