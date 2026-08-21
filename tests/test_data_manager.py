from __future__ import annotations

from datetime import datetime, timezone

import pytest

from core.errors import ApplicationError
from data.base import MarketDataProvider
from data.manager import DataManager
from data.models import Candle


class FakeProvider(MarketDataProvider):
    name = "fake"

    def __init__(
        self,
        candles: list[Candle] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.candles = candles or []
        self.error = error

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> list[Candle]:

        if self.error is not None:
            raise self.error

        return self.candles[:limit]


def make_candle(
    minute: int,
    close: float = 1.1000,
) -> Candle:
    return Candle(
        symbol="EUR_USD",
        timestamp=datetime(
            2026,
            1,
            1,
            12,
            minute,
            tzinfo=timezone.utc,
        ),
        open=1.0900,
        high=1.1100,
        low=1.0800,
        close=close,
        volume=100.0,
    )


def test_register_provider() -> None:
    manager = DataManager()
    provider = FakeProvider()

    manager.register(provider)

    assert manager.list_providers() == [
        "fake"
    ]


def test_get_registered_provider() -> None:
    manager = DataManager()
    provider = FakeProvider()

    manager.register(provider)

    result = manager.get_provider(
        "fake"
    )

    assert result is provider


def test_duplicate_provider() -> None:
    manager = DataManager()

    manager.register(
        FakeProvider()
    )

    with pytest.raises(
        ApplicationError
    ):
        manager.register(
            FakeProvider()
        )


def test_missing_provider() -> None:
    manager = DataManager()

    with pytest.raises(
        ApplicationError
    ):
        manager.get_provider(
            "missing"
        )


def test_empty_provider_name() -> None:
    class EmptyNameProvider(
        MarketDataProvider
    ):
        name = ""

        async def get_candles(
            self,
            symbol: str,
            timeframe: str,
            limit: int = 100,
        ) -> list[Candle]:
            return []

    manager = DataManager()

    with pytest.raises(
        ApplicationError
    ):
        manager.register(
            EmptyNameProvider()
        )


@pytest.mark.asyncio
async def test_get_candles() -> None:
    candles = [
        make_candle(1),
        make_candle(2),
        make_candle(3),
    ]

    provider = FakeProvider(
        candles=candles
    )

    manager = DataManager()

    manager.register(provider)

    result = await manager.get_candles(
        provider_name="fake",
        symbol="EUR_USD",
        timeframe="M15",
        limit=100,
    )

    assert result == candles


@pytest.mark.asyncio
async def test_get_candles_respects_limit() -> None:
    candles = [
        make_candle(1),
        make_candle(2),
        make_candle(3),
    ]

    provider = FakeProvider(
        candles=candles
    )

    manager = DataManager()

    manager.register(provider)

    result = await manager.get_candles(
        provider_name="fake",
        symbol="EUR_USD",
        timeframe="M15",
        limit=2,
    )

    assert len(result) == 2
    assert result == candles[:2]


@pytest.mark.asyncio
async def test_get_candles_empty_result() -> None:
    manager = DataManager()

    manager.register(
        FakeProvider()
    )

    result = await manager.get_candles(
        provider_name="fake",
        symbol="EUR_USD",
        timeframe="M15",
        limit=100,
    )

    assert result == []


@pytest.mark.asyncio
async def test_get_candles_invalid_limit() -> None:
    manager = DataManager()

    manager.register(
        FakeProvider()
    )

    with pytest.raises(
        ValueError,
        match="limit must be greater than zero",
    ):
        await manager.get_candles(
            provider_name="fake",
            symbol="EUR_USD",
            timeframe="M15",
            limit=0,
        )


@pytest.mark.asyncio
async def test_get_candles_negative_limit() -> None:
    manager = DataManager()

    manager.register(
        FakeProvider()
    )

    with pytest.raises(
        ValueError,
        match="limit must be greater than zero",
    ):
        await manager.get_candles(
            provider_name="fake",
            symbol="EUR_USD",
            timeframe="M15",
            limit=-1,
        )


@pytest.mark.asyncio
async def test_provider_error_is_propagated() -> None:
    original_error = RuntimeError(
        "provider failure"
    )

    manager = DataManager()

    manager.register(
        FakeProvider(
            error=original_error
        )
    )

    with pytest.raises(
        RuntimeError,
        match="provider failure",
    ):
        await manager.get_candles(
            provider_name="fake",
            symbol="EUR_USD",
            timeframe="M15",
            limit=100,
        )


def test_list_providers_empty() -> None:
    manager = DataManager()

    assert manager.list_providers() == []


def test_multiple_providers() -> None:
    manager = DataManager()

    first = FakeProvider()
    first.name = "first"

    second = FakeProvider()
    second.name = "second"

    manager.register(first)
    manager.register(second)

    assert manager.list_providers() == [
        "first",
        "second",
    ]
