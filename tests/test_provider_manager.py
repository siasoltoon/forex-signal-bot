
from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock

import pytest

from data.models import Candle
from data.provider_manager import (
    ProviderManager,
)


# ----------------------------------------------------------------------
# Test helpers
# ----------------------------------------------------------------------


def make_candle(
    timestamp: int,
    *,
    symbol: str = "EUR_USD",
    open_price: float = 1.1000,
    high: float = 1.1200,
    low: float = 1.0900,
    close: float = 1.1100,
    volume: float = 100.0,
) -> Candle:
    """
    Create a deterministic Candle for tests.

    The helper tries the project's existing Candle constructor
    contract without modifying the production model.
    """

    return Candle(
        symbol=symbol,
        timestamp=timestamp,
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=volume,
    )


class FakeProvider:
    """
    Minimal provider double used by the manager tests.

    It intentionally exposes only get_candles(), which is the
    contract required by MarketDataProvider.
    """

    def __init__(
        self,
        responses: list[object] | None = None,
    ) -> None:
        self.responses = (
            list(responses)
            if responses is not None
            else []
        )

        self.calls = 0

    async def get_candles(
        self,
        *,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> list[Candle]:
        self.calls += 1

        if not self.responses:
            return []

        response = self.responses.pop(0)

        if isinstance(
            response,
            Exception,
        ):
            raise response

        return response


# ----------------------------------------------------------------------
# Factory patch helper
# ----------------------------------------------------------------------


def patch_factory(
    monkeypatch,
    providers: dict[str, object],
) -> None:
    """
    Replace ProviderFactory.create() with deterministic test providers.
    """

    def fake_create(
        provider_name: str,
    ):
        return providers[
            provider_name
        ]

    monkeypatch.setattr(
        "data.provider_manager.ProviderFactory.create",
        fake_create,
    )


# ----------------------------------------------------------------------
# Basic success
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_manager_uses_first_provider(
    monkeypatch,
) -> None:
    candles = [
        make_candle(1),
        make_candle(2),
        make_candle(3),
    ]

    oanda = FakeProvider(
        [candles]
    )

    finnhub = FakeProvider(
        [candles]
    )

    patch_factory(
        monkeypatch,
        {
            "oanda": oanda,
            "finnhub": finnhub,
        },
    )

    manager = ProviderManager(
        providers=[
            "oanda",
            "finnhub",
        ],
        retries=0,
        cooldown_seconds=0,
    )

    result = await manager.get_candles(
        symbol="EUR_USD",
        timeframe="M15",
        limit=10,
    )

    assert result == candles

    assert oanda.calls == 1
    assert finnhub.calls == 0


# ----------------------------------------------------------------------
# Retry
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_manager_retries_failed_provider(
    monkeypatch,
) -> None:
    candles = [
        make_candle(1),
    ]

    provider = FakeProvider(
        [
            RuntimeError("temporary failure"),
            RuntimeError("temporary failure"),
            candles,
        ]
    )

    patch_factory(
        monkeypatch,
        {
            "oanda": provider,
        },
    )

    manager = ProviderManager(
        providers=["oanda"],
        retries=2,
        retry_delay=0,
        cooldown_seconds=0,
    )

    result = await manager.get_candles(
        symbol="EUR_USD",
        timeframe="M15",
        limit=10,
    )

    assert result == candles
    assert provider.calls == 3


# ----------------------------------------------------------------------
# Retry exhausted -> fallback
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_manager_falls_back_after_retries(
    monkeypatch,
) -> None:
    candles = [
        make_candle(1),
        make_candle(2),
    ]

    first = FakeProvider(
        [
            RuntimeError("oanda down"),
            RuntimeError("oanda down"),
        ]
    )

    second = FakeProvider(
        [
            candles,
        ]
    )

    patch_factory(
        monkeypatch,
        {
            "oanda": first,
            "finnhub": second,
        },
    )

    manager = ProviderManager(
        providers=[
            "oanda",
            "finnhub",
        ],
        retries=1,
        retry_delay=0,
        cooldown_seconds=0,
    )

    result = await manager.get_candles(
        symbol="EUR_USD",
        timeframe="M15",
        limit=10,
    )

    assert result == candles

    assert first.calls == 2
    assert second.calls == 1


# ----------------------------------------------------------------------
# Full provider failure
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_manager_raises_when_all_providers_fail(
    monkeypatch,
) -> None:
    first = FakeProvider(
        [
            RuntimeError("oanda failure"),
        ]
    )

    second = FakeProvider(
        [
            RuntimeError("finnhub failure"),
        ]
    )

    patch_factory(
        monkeypatch,
        {
            "oanda": first,
            "finnhub": second,
        },
    )

    manager = ProviderManager(
        providers=[
            "oanda",
            "finnhub",
        ],
        retries=0,
        retry_delay=0,
        cooldown_seconds=0,
    )

    with pytest.raises(
        Exception,
        match="All market data providers failed",
    ):
        await manager.get_candles(
            symbol="EUR_USD",
            timeframe="M15",
            limit=10,
        )


# ----------------------------------------------------------------------
# Cooldown
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_manager_skips_provider_in_cooldown(
    monkeypatch,
) -> None:
    first = FakeProvider(
        [
            RuntimeError("provider unavailable"),
        ]
    )

    second_candles = [
        make_candle(1),
    ]

    second = FakeProvider(
        [
            second_candles,
        ]
    )

    patch_factory(
        monkeypatch,
        {
            "oanda": first,
            "finnhub": second,
        },
    )

    manager = ProviderManager(
        providers=[
            "oanda",
            "finnhub",
        ],
        retries=0,
        retry_delay=0,
        cooldown_seconds=60,
    )

    # First request:
    # OANDA fails and enters cooldown.
    result = await manager.get_candles(
        symbol="EUR_USD",
        timeframe="M15",
        limit=10,
    )

    assert result == second_candles
    assert first.calls == 1
    assert second.calls == 1

    # Second request:
    # OANDA must be skipped because it is still in cooldown.
    result = await manager.get_candles(
        symbol="EUR_USD",
        timeframe="M15",
        limit=10,
    )

    assert result == second_candles

    assert first.calls == 1
    assert second.calls == 2


# ----------------------------------------------------------------------
# Cooldown clearing
# ----------------------------------------------------------------------


def test_manager_can_clear_provider_cooldown(
    monkeypatch,
) -> None:
    provider = FakeProvider()

    patch_factory(
        monkeypatch,
        {
            "oanda": provider,
        },
    )

    manager = ProviderManager(
        providers=["oanda"],
        retries=0,
        retry_delay=0,
        cooldown_seconds=60,
    )

    manager._cooldowns["oanda"] = (
        999999999999.0
    )

    assert manager._is_in_cooldown(
        "oanda"
    )

    manager.clear_cooldown(
        "oanda"
    )

    assert not manager._is_in_cooldown(
        "oanda"
    )


def test_manager_can_clear_all_cooldowns(
    monkeypatch,
) -> None:
    provider = FakeProvider()

    patch_factory(
        monkeypatch,
        {
            "oanda": provider,
        },
    )

    manager = ProviderManager(
        providers=["oanda"],
        retries=0,
        retry_delay=0,
        cooldown_seconds=60,
    )

    manager._cooldowns["oanda"] = (
        999999999999.0
    )

    manager.clear_all_cooldowns()

    assert manager.status()["cooldowns"] == {}


# ----------------------------------------------------------------------
# Candle ordering
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_manager_normalizes_candle_order(
    monkeypatch,
) -> None:
    candles = [
        make_candle(3),
        make_candle(1),
        make_candle(2),
    ]

    provider = FakeProvider(
        [candles]
    )

    patch_factory(
        monkeypatch,
        {
            "oanda": provider,
        },
    )

    manager = ProviderManager(
        providers=["oanda"],
        retries=0,
        cooldown_seconds=0,
    )

    result = await manager.get_candles(
        symbol="EUR_USD",
        timeframe="M15",
        limit=10,
    )

    assert [
        candle.timestamp
        for candle in result
    ] == [
        1,
        2,
        3,
    ]


# ----------------------------------------------------------------------
# Duplicate candle removal
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_manager_removes_duplicate_timestamps(
    monkeypatch,
) -> None:
    candles = [
        make_candle(1),
        make_candle(2),
        make_candle(2),
        make_candle(3),
    ]

    provider = FakeProvider(
        [candles]
    )

    patch_factory(
        monkeypatch,
        {
            "oanda": provider,
        },
    )

    manager = ProviderManager(
        providers=["oanda"],
        retries=0,
        cooldown_seconds=0,
    )

    result = await manager.get_candles(
        symbol="EUR_USD",
        timeframe="M15",
        limit=10,
    )

    assert [
        candle.timestamp
        for candle in result
    ] == [
        1,
        2,
        3,
    ]


# ----------------------------------------------------------------------
# Limit enforcement
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_manager_respects_limit(
    monkeypatch,
) -> None:
    candles = [
        make_candle(1),
        make_candle(2),
        make_candle(3),
        make_candle(4),
        make_candle(5),
    ]

    provider = FakeProvider(
        [candles]
    )

    patch_factory(
        monkeypatch,
        {
            "oanda": provider,
        },
    )

    manager = ProviderManager(
        providers=["oanda"],
        retries=0,
        cooldown_seconds=0,
    )

    result = await manager.get_candles(
        symbol="EUR_USD",
        timeframe="M15",
        limit=3,
    )

    assert [
        candle.timestamp
        for candle in result
    ] == [
        3,
        4,
        5,
    ]


# ----------------------------------------------------------------------
# Provider priority
# ----------------------------------------------------------------------


def test_manager_preserves_provider_priority(
    monkeypatch,
) -> None:
    providers = {
        "oanda": FakeProvider(),
        "finnhub": FakeProvider(),
        "alphavantage": FakeProvider(),
    }

    patch_factory(
        monkeypatch,
        providers,
    )

    manager = ProviderManager(
        providers=[
            "finnhub",
            "oanda",
            "alphavantage",
        ]
    )

    assert manager.providers == (
        "finnhub",
        "oanda",
        "alphavantage",
    )


# ----------------------------------------------------------------------
# Duplicate providers
# ----------------------------------------------------------------------


def test_manager_removes_duplicate_providers(
    monkeypatch,
) -> None:
    providers = {
        "oanda": FakeProvider(),
        "finnhub": FakeProvider(),
    }

    patch_factory(
        monkeypatch,
        providers,
    )

    manager = ProviderManager(
        providers=[
            "oanda",
            "oanda",
            "finnhub",
            "finnhub",
        ]
    )

    assert manager.providers == (
        "oanda",
        "finnhub",
    )


# ----------------------------------------------------------------------
# Invalid configuration
# ----------------------------------------------------------------------


def test_manager_rejects_empty_provider_list() -> None:
    with pytest.raises(
        ValueError,
        match="At least one provider",
    ):
        ProviderManager(
            providers=[]
        )


def test_manager_rejects_negative_retries() -> None:
    with pytest.raises(
        ValueError,
        match="retries cannot be negative",
    ):
        ProviderManager(
            retries=-1
        )


@pytest.mark.asyncio
async def test_manager_rejects_invalid_limit(
    monkeypatch,
) -> None:
    provider = FakeProvider()

    patch_factory(
        monkeypatch,
        {
            "oanda": provider,
        },
    )

    manager = ProviderManager(
        providers=["oanda"],
        retries=0,
        cooldown_seconds=0,
    )

    with pytest.raises(
        ValueError,
        match="limit must be greater than zero",
    ):
        await manager.get_candles(
            symbol="EUR_USD",
            timeframe="M15",
            limit=0,
        )


# ----------------------------------------------------------------------
# Failure reporting
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_manager_records_failures(
    monkeypatch,
) -> None:
    provider = FakeProvider(
        [
            RuntimeError("temporary failure"),
        ]
    )

    patch_factory(
        monkeypatch,
        {
            "oanda": provider,
        },
    )

    manager = ProviderManager(
        providers=["oanda"],
        retries=0,
        retry_delay=0,
        cooldown_seconds=0,
    )

    with pytest.raises(Exception):
        await manager.get_candles(
            symbol="EUR_USD",
            timeframe="M15",
            limit=10,
        )

    failures = manager.last_failures

    assert len(failures) == 1
    assert failures[0].provider == "oanda"
    assert failures[0].attempt == 1
    assert failures[0].error_type == "RuntimeError"
    assert "temporary failure" in failures[0].message


# ----------------------------------------------------------------------
# Status
# ----------------------------------------------------------------------


def test_manager_status(
    monkeypatch,
) -> None:
    provider = FakeProvider()

    patch_factory(
        monkeypatch,
        {
            "oanda": provider,
        },
    )

    manager = ProviderManager(
        providers=["oanda"],
        retries=2,
        retry_delay=0.5,
        cooldown_seconds=30,
    )

    status = manager.status()

    assert status["providers"] == [
        "oanda"
    ]

    assert status["retries"] == 2
    assert status["retry_delay"] == 0.5
    assert status["cooldown_seconds"] == 30.0
    assert status["cached_instances"] == []

