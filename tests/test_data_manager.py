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


def make_candle(
    minute: int,
    close: float = 1.1000,
    symbol: str = "EUR_USD",
) -> Candle:
    return Candle(
        symbol=symbol,
        timestamp=datetime(
            2026,
            1,
            1,
            12,
            minute,
            tzinfo=timezone.utc,
        ),
        open=1.0900,
        high=max(1.1100, close),
        low=1.0800,
        close=close,
        volume=100.0,
    )


def test_register_provider() -> None:
    manager = DataManager()
    provider = FakeProvider()

    manager.register(provider)

    assert manager.list_providers() == ["fake"]
    assert manager.provider_count() == 1
    assert manager.default_provider == "fake"


def test_get_registered_provider() -> None:
    manager = DataManager()
    provider = FakeProvider()

    manager.register(provider)

    result = manager.get_provider(" FAKE ")

    assert result is provider


def test_duplicate_provider() -> None:
    manager = DataManager()
    manager.register(FakeProvider())

    with pytest.raises(ApplicationError, match="Provider already registered"):
        manager.register(FakeProvider())


def test_missing_provider() -> None:
    manager = DataManager()

    with pytest.raises(ApplicationError, match="provider not found"):
        manager.get_provider("missing")


def test_empty_provider_name() -> None:
    class EmptyNameProvider(MarketDataProvider):
        name = ""

        async def get_candles(
            self,
            symbol: str,
            timeframe: str,
            limit: int = 100,
        ) -> list[Candle]:
            return []

    manager = DataManager()

    with pytest.raises(ApplicationError, match="Provider name cannot be empty"):
        manager.register(EmptyNameProvider())


def test_non_provider_registration_is_rejected() -> None:
    manager = DataManager()

    with pytest.raises(TypeError, match="provider must implement MarketDataProvider"):
        manager.register(object())  # type: ignore[arg-type]


def test_default_provider_can_be_selected_explicitly() -> None:
    manager = DataManager()

    first = FakeProvider()
    first.name = "first"
    second = FakeProvider()
    second.name = "second"

    manager.register(first)
    manager.register(second)

    assert manager.default_provider == "first"
    assert manager.get_default_provider() is first

    manager.set_default_provider(" SECOND ")

    assert manager.default_provider == "second"
    assert manager.get_default_provider() is second


def test_set_unknown_default_provider_is_rejected() -> None:
    manager = DataManager()

    with pytest.raises(
        ApplicationError,
        match="Cannot set unknown provider as default",
    ):
        manager.set_default_provider("missing")


def test_get_default_provider_without_configuration_is_rejected() -> None:
    manager = DataManager()

    with pytest.raises(
        ApplicationError,
        match="No default market data provider",
    ):
        manager.get_default_provider()


def test_unregister_provider_updates_default() -> None:
    manager = DataManager()

    first = FakeProvider()
    first.name = "first"
    second = FakeProvider()
    second.name = "second"

    manager.register(first)
    manager.register(second)
    manager.unregister(" FIRST ")

    assert manager.list_providers() == ["second"]
    assert manager.default_provider == "second"
    assert manager.get_default_provider() is second


def test_unregister_missing_provider_is_rejected() -> None:
    manager = DataManager()

    with pytest.raises(
        ApplicationError,
        match="Market data provider not found",
    ):
        manager.unregister("missing")


def test_unregister_last_provider_clears_default() -> None:
    manager = DataManager()
    manager.register(FakeProvider())

    manager.unregister("fake")

    assert manager.list_providers() == []
    assert manager.provider_count() == 0
    assert manager.default_provider is None


@pytest.mark.asyncio
async def test_get_candles() -> None:
    candles = [make_candle(1), make_candle(2), make_candle(3)]
    provider = FakeProvider(candles=candles)
    manager = DataManager()
    manager.register(provider)

    result = await manager.get_candles(
        provider_name="fake",
        symbol=" eur_usd ",
        timeframe=" m15 ",
        limit=100,
    )

    assert result == candles
    assert provider.calls == 1


@pytest.mark.asyncio
async def test_get_candles_uses_default_provider_when_name_is_none() -> None:
    candles = [make_candle(1)]
    provider = FakeProvider(candles=candles)
    manager = DataManager()
    manager.register(provider)

    result = await manager.get_candles(
        provider_name=None,
        symbol="EUR_USD",
        timeframe="M15",
        limit=100,
    )

    assert result == candles
    assert provider.calls == 1


@pytest.mark.asyncio
async def test_get_candles_respects_limit() -> None:
    candles = [make_candle(1), make_candle(2), make_candle(3)]
    provider = FakeProvider(candles=candles)
    manager = DataManager()
    manager.register(provider)

    result = await manager.get_candles(
        provider_name="fake",
        symbol="EUR_USD",
        timeframe="M15",
        limit=2,
    )

    assert result == candles[:2]


@pytest.mark.asyncio
async def test_get_candles_empty_result() -> None:
    manager = DataManager()
    manager.register(FakeProvider())

    result = await manager.get_candles(
        provider_name="fake",
        symbol="EUR_USD",
        timeframe="M15",
        limit=100,
    )

    assert result == []


@pytest.mark.asyncio
@pytest.mark.parametrize("limit", [0, -1])
async def test_get_candles_rejects_non_positive_limit(limit: int) -> None:
    manager = DataManager()
    manager.register(FakeProvider())

    with pytest.raises(ValueError, match="limit must be greater than zero"):
        await manager.get_candles(
            provider_name="fake",
            symbol="EUR_USD",
            timeframe="M15",
            limit=limit,
        )


@pytest.mark.asyncio
async def test_get_candles_rejects_limit_above_maximum() -> None:
    manager = DataManager()
    manager.register(FakeProvider())

    with pytest.raises(ValueError, match="limit cannot exceed"):
        await manager.get_candles(
            provider_name="fake",
            symbol="EUR_USD",
            timeframe="M15",
            limit=DataManager.MAX_LIMIT + 1,
        )


@pytest.mark.asyncio
async def test_get_candles_rejects_invalid_symbol() -> None:
    manager = DataManager()
    manager.register(FakeProvider())

    with pytest.raises(ValueError, match="symbol cannot be empty"):
        await manager.get_candles(
            provider_name="fake",
            symbol="   ",
            timeframe="M15",
            limit=10,
        )


@pytest.mark.asyncio
async def test_get_candles_rejects_invalid_timeframe() -> None:
    manager = DataManager()
    manager.register(FakeProvider())

    with pytest.raises(ValueError, match="timeframe cannot be empty"):
        await manager.get_candles(
            provider_name="fake",
            symbol="EUR_USD",
            timeframe="   ",
            limit=10,
        )


@pytest.mark.asyncio
async def test_provider_error_is_wrapped() -> None:
    original_error = RuntimeError("provider failure")
    manager = DataManager()
    manager.register(FakeProvider(error=original_error))

    with pytest.raises(
        ApplicationError,
        match="Failed to fetch market candles",
    ) as exc:
        await manager.get_candles(
            provider_name="fake",
            symbol="EUR_USD",
            timeframe="M15",
            limit=100,
        )

    assert isinstance(exc.value.__cause__, RuntimeError)
    assert str(exc.value.__cause__) == "provider failure"


@pytest.mark.asyncio
async def test_invalid_provider_candle_data_is_wrapped() -> None:
    class InvalidProvider(MarketDataProvider):
        name = "invalid"

        async def get_candles(
            self,
            symbol: str,
            timeframe: str,
            limit: int = 100,
        ) -> list[Candle]:
            return ["invalid"]  # type: ignore[list-item]

    manager = DataManager()
    manager.register(InvalidProvider())

    with pytest.raises(
        ApplicationError,
        match="Provider returned invalid candle data",
    ) as exc:
        await manager.get_candles(
            provider_name="invalid",
            symbol="EUR_USD",
            timeframe="M15",
            limit=10,
        )

    assert isinstance(exc.value.__cause__, TypeError)


@pytest.mark.asyncio
async def test_get_candles_normalizes_order_and_duplicates() -> None:
    first = make_candle(1, close=1.10)
    second = make_candle(2, close=1.20)
    duplicate = make_candle(2, close=1.25)
    third = make_candle(3, close=1.30)

    provider = FakeProvider(
        candles=[third, first, second, duplicate],
    )
    manager = DataManager()
    manager.register(provider)

    result = await manager.get_candles(
        provider_name="fake",
        symbol="EUR_USD",
        timeframe="M15",
        limit=10,
    )

    assert [c.timestamp for c in result] == [
        first.timestamp,
        duplicate.timestamp,
        third.timestamp,
    ]
    assert result[1].close == 1.25


@pytest.mark.asyncio
async def test_fallback_returns_first_successful_non_empty_result() -> None:
    first = FakeProvider(error=RuntimeError("first failed"))
    first.name = "first"
    second_candles = [make_candle(1), make_candle(2)]
    second = FakeProvider(candles=second_candles)
    second.name = "second"

    manager = DataManager()
    manager.register(first)
    manager.register(second)

    result = await manager.get_candles_with_fallback(
        symbol="EUR_USD",
        timeframe="M15",
        limit=10,
    )

    assert result == second_candles
    assert first.calls == 1
    assert second.calls == 1


@pytest.mark.asyncio
async def test_fallback_skips_empty_provider() -> None:
    first = FakeProvider()
    first.name = "first"
    second_candles = [make_candle(1)]
    second = FakeProvider(candles=second_candles)
    second.name = "second"

    manager = DataManager()
    manager.register(first)
    manager.register(second)

    result = await manager.get_candles_with_fallback(
        symbol="EUR_USD",
        timeframe="M15",
        limit=10,
    )

    assert result == second_candles
    assert first.calls == 1
    assert second.calls == 1


@pytest.mark.asyncio
async def test_fallback_can_use_explicit_provider_order() -> None:
    first = FakeProvider(candles=[make_candle(1)])
    first.name = "first"
    second = FakeProvider(candles=[make_candle(2)])
    second.name = "second"

    manager = DataManager()
    manager.register(first)
    manager.register(second)

    result = await manager.get_candles_with_fallback(
        symbol="EUR_USD",
        timeframe="M15",
        limit=10,
        providers=[" SECOND "],
    )

    assert result == [make_candle(2)]
    assert first.calls == 0
    assert second.calls == 1


@pytest.mark.asyncio
async def test_fallback_rejects_unknown_only_provider_list() -> None:
    manager = DataManager()
    manager.register(FakeProvider())

    with pytest.raises(ApplicationError, match="All market data providers failed"):
        await manager.get_candles_with_fallback(
            symbol="EUR_USD",
            timeframe="M15",
            limit=10,
            providers=["missing"],
        )


@pytest.mark.asyncio
async def test_fallback_raises_when_no_providers_exist() -> None:
    manager = DataManager()

    with pytest.raises(ApplicationError, match="No market data providers"):
        await manager.get_candles_with_fallback(
            symbol="EUR_USD",
            timeframe="M15",
            limit=10,
        )


def test_list_providers_empty() -> None:
    manager = DataManager()
    assert manager.list_providers() == []
    assert manager.provider_count() == 0


def test_multiple_providers() -> None:
    manager = DataManager()

    first = FakeProvider()
    first.name = "first"
    second = FakeProvider()
    second.name = "second"

    manager.register(first)
    manager.register(second)

    assert manager.list_providers() == ["first", "second"]
    assert manager.provider_count() == 2
