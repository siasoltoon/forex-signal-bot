from __future__ import annotations

from datetime import datetime, timezone

import pytest

from core.errors import ApplicationError
from data.base import MarketDataProvider
from data.manager import DataManager
from data.models import Candle


class ContractProvider(MarketDataProvider):
    def __init__(
        self,
        name: str,
        candles: list[Candle] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.name = name
        self.candles = candles if candles is not None else []
        self.error = error
        self.calls = 0

    def is_configured(self) -> bool:
        return True

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


def make_candle(minute: int, close: float = 1.1000) -> Candle:
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
        high=max(1.1100, close),
        low=1.0800,
        close=close,
        volume=100.0,
    )


@pytest.mark.asyncio
async def test_explicit_delegation_calls_only_selected_provider() -> None:
    first = ContractProvider("first", [make_candle(1)])
    second = ContractProvider("second", [make_candle(2)])
    manager = DataManager()
    manager.register(first)
    manager.register(second)

    result = await manager.get_candles(
        provider_name=" SECOND ",
        symbol=" eur_usd ",
        timeframe=" m15 ",
        limit=10,
    )

    assert result == [make_candle(2)]
    assert first.calls == 0
    assert second.calls == 1


@pytest.mark.asyncio
async def test_explicit_delegation_does_not_fallback_after_provider_error() -> None:
    first = ContractProvider("first", error=RuntimeError("selected failure"))
    second = ContractProvider("second", [make_candle(2)])
    manager = DataManager()
    manager.register(first)
    manager.register(second)

    with pytest.raises(
        ApplicationError,
        match="Failed to fetch market candles",
    ) as exc:
        await manager.get_candles(
            provider_name="first",
            symbol="EUR_USD",
            timeframe="M15",
            limit=10,
        )

    assert isinstance(exc.value.__cause__, RuntimeError)
    assert str(exc.value.__cause__) == "selected failure"
    assert first.calls == 1
    assert second.calls == 0


@pytest.mark.asyncio
async def test_explicit_delegation_allows_empty_result_without_fallback() -> None:
    first = ContractProvider("first")
    second = ContractProvider("second", [make_candle(2)])
    manager = DataManager()
    manager.register(first)
    manager.register(second)

    result = await manager.get_candles(
        provider_name="first",
        symbol="EUR_USD",
        timeframe="M15",
        limit=10,
    )

    assert result == []
    assert first.calls == 1
    assert second.calls == 0


@pytest.mark.asyncio
async def test_explicit_delegation_uses_default_provider_through_same_contract() -> None:
    first = ContractProvider("first", [make_candle(1)])
    second = ContractProvider("second", [make_candle(2)])
    manager = DataManager()
    manager.register(first)
    manager.register(second)
    manager.set_default_provider("second")

    result = await manager.get_candles(
        provider_name=None,
        symbol="EUR_USD",
        timeframe="M15",
        limit=10,
    )

    assert result == [make_candle(2)]
    assert first.calls == 0
    assert second.calls == 1


@pytest.mark.asyncio
async def test_explicit_delegation_preserves_provider_application_error() -> None:
    original = ApplicationError(
        "Provider authentication failed.",
        {"provider": "first"},
    )
    provider = ContractProvider("first", error=original)
    manager = DataManager()
    manager.register(provider)

    with pytest.raises(ApplicationError, match="Provider authentication failed") as exc:
        await manager.get_candles(
            provider_name="first",
            symbol="EUR_USD",
            timeframe="M15",
            limit=10,
        )

    assert exc.value is original
    assert provider.calls == 1
