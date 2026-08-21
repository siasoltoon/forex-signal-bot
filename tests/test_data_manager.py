from __future__ import annotations

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
        self.candles = (
            candles
            if candles is not None
            else []
        )

        self.error = error

        self.calls = 0

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> list[Candle]:

        self.calls += 1

        if self.error is not None:
            raise self.error

        return self.candles[:limit]


def create_candle(
    symbol: str = "EUR_USD",
) -> Candle:

    from datetime import datetime, timezone

    return Candle(
        symbol=symbol,
        timestamp=datetime.now(
            timezone.utc
        ),
        open=1.1000,
        high=1.1050,
        low=1.0950,
        close=1.1020,
        volume=1000.0,
    )


def test_register_provider() -> None:

    manager = DataManager()

    provider = FakeProvider()

    manager.register(
        provider
    )

    assert (
        manager.list_providers()
        == ["fake"]
    )


def test_first_registered_provider_becomes_default() -> None:

    manager = DataManager()

    manager.register(
        FakeProvider()
    )

    assert (
        manager.default_provider
        == "fake"
    )

    assert (
        manager.get_default_provider()
        is manager.get_provider("fake")
    )


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


def test_has_provider() -> None:

    manager = DataManager()

    manager.register(
        FakeProvider()
    )

    assert (
        manager.has_provider("fake")
        is True
    )

    assert (
        manager.has_provider("missing")
        is False
    )


def test_provider_name_is_normalized() -> None:

    manager = DataManager()

    provider = FakeProvider()

    manager.register(
        provider
    )

    assert manager.has_provider(
        "FAKE"
    )

    assert manager.get_provider(
        " Fake "
    ) is provider


def test_set_default_provider() -> None:

    manager = DataManager()

    first = FakeProvider()

    second = FakeProvider()

    second.name = "second"

    manager.register(first)
    manager.register(second)

    manager.set_default_provider(
        "second"
    )

    assert (
        manager.default_provider
        == "second"
    )

    assert (
        manager.get_default_provider()
        is second
    )


def test_unknown_default_provider() -> None:

    manager = DataManager()

    with pytest.raises(
        ApplicationError
    ):
        manager.set_default_provider(
            "missing"
        )


@pytest.mark.asyncio
async def test_get_candles_from_provider() -> None:

    candles = [
        create_candle(),
        create_candle(),
        create_candle(),
    ]

    provider = FakeProvider(
        candles=candles
    )

    manager = DataManager()

    manager.register(
        provider
    )

    result = await manager.get_candles(
        provider_name="fake",
        symbol="EUR_USD",
        timeframe="M15",
        limit=2,
    )

    assert len(result) == 2

    assert (
        provider.calls
        == 1
    )


@pytest.mark.asyncio
async def test_get_candles_uses_default_provider() -> None:

    candles = [
        create_candle(),
    ]

    provider = FakeProvider(
        candles=candles
    )

    manager = DataManager()

    manager.register(
        provider
    )

    result = await manager.get_candles(
        provider_name=None,
        symbol="EUR_USD",
        timeframe="M15",
    )

    assert len(result) == 1

    assert (
        provider.calls
        == 1
    )


@pytest.mark.asyncio
async def test_get_candles_invalid_limit() -> None:

    manager = DataManager()

    manager.register(
        FakeProvider()
    )

    with pytest.raises(
        ValueError
    ):
        await manager.get_candles(
            provider_name="fake",
            symbol="EUR_USD",
            timeframe="M15",
            limit=0,
        )


@pytest.mark.asyncio
async def test_get_candles_empty_symbol() -> None:

    manager = DataManager()

    manager.register(
        FakeProvider()
    )

    with pytest.raises(
        ValueError
    ):
        await manager.get_candles(
            provider_name="fake",
            symbol="",
            timeframe="M15",
        )


@pytest.mark.asyncio
async def test_get_candles_empty_timeframe() -> None:

    manager = DataManager()

    manager.register(
        FakeProvider()
    )

    with pytest.raises(
        ValueError
    ):
        await manager.get_candles(
            provider_name="fake",
            symbol="EUR_USD",
            timeframe="",
        )


@pytest.mark.asyncio
async def test_provider_failure_is_wrapped() -> None:

    provider = FakeProvider(
        error=RuntimeError(
            "API unavailable"
        )
    )

    manager = DataManager()

    manager.register(
        provider
    )

    with pytest.raises(
        ApplicationError
    ):
        await manager.get_candles(
            provider_name="fake",
            symbol="EUR_USD",
            timeframe="M15",
        )


def test_unregister_provider() -> None:

    manager = DataManager()

    manager.register(
        FakeProvider()
    )

    manager.unregister(
        "fake"
    )

    assert (
        manager.list_providers()
        == []
    )

    assert (
        manager.default_provider
        is None
    )


def test_provider_count() -> None:

    manager = DataManager()

    assert (
        manager.provider_count()
        == 0
    )

    manager.register(
        FakeProvider()
    )

    assert (
        manager.provider_count()
        == 1
    )


@pytest.mark.asyncio
async def test_fallback_uses_next_provider() -> None:

    failing_provider = FakeProvider(
        error=RuntimeError(
            "Primary provider failed"
        )
    )

    working_provider = FakeProvider(
        candles=[
            create_candle()
        ]
    )

    working_provider.name = "working"

    manager = DataManager()

    manager.register(
        failing_provider
    )

    manager.register(
        working_provider
    )

    result = await manager.get_candles_with_fallback(
        symbol="EUR_USD",
        timeframe="M15",
        limit=100,
        providers=[
            "fake",
            "working",
        ],
    )

    assert len(result) == 1

    assert (
        failing_provider.calls
        == 1
    )

    assert (
        working_provider.calls
        == 1
    )


@pytest.mark.asyncio
async def test_fallback_all_providers_fail() -> None:

    first = FakeProvider(
        error=RuntimeError(
            "First failed"
        )
    )

    second = FakeProvider(
        error=RuntimeError(
            "Second failed"
        )
    )

    second.name = "second"

    manager = DataManager()

    manager.register(first)
    manager.register(second)

    with pytest.raises(
        ApplicationError
    ):
        await manager.get_candles_with_fallback(
            symbol="EUR_USD",
            timeframe="M15",
            providers=[
                "fake",
                "second",
            ],
        )


@pytest.mark.asyncio
async def test_fallback_rejects_empty_result() -> None:

    empty_provider = FakeProvider(
        candles=[]
    )

    working_provider = FakeProvider(
        candles=[
            create_candle()
        ]
    )

    working_provider.name = "working"

    manager = DataManager()

    manager.register(
        empty_provider
    )

    manager.register(
        working_provider
    )

    result = await manager.get_candles_with_fallback(
        symbol="EUR_USD",
        timeframe="M15",
        providers=[
            "fake",
            "working",
        ],
    )

    assert len(result) == 1

    assert (
        empty_provider.calls
        == 1
    )

    assert (
        working_provider.calls
        == 1
    )
