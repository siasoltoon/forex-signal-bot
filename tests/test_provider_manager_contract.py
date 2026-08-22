from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from core.errors import ApplicationError
from data.models import Candle
from data.provider_manager import ProviderManager


class FakeProvider:
    def __init__(self, name: str, result=None, error: Exception | None = None):
        self.name = name
        self.get_candles = AsyncMock()
        if error is not None:
            self.get_candles.side_effect = error
        else:
            self.get_candles.return_value = result


def candle(minute: int, close: float = 1.1005) -> Candle:
    return Candle(
        symbol="EURUSD",
        timestamp=datetime(2026, 1, 1, 0, minute, tzinfo=timezone.utc),
        open=1.1000,
        high=1.1010,
        low=1.0990,
        close=close,
        volume=100.0,
    )


@pytest.mark.asyncio
async def test_manager_uses_provider_priority_and_forwards_request():
    first = FakeProvider("first", [candle(1)])
    second = FakeProvider("second", [candle(2)])

    manager = ProviderManager(
        providers=[first, second],
        retries=0,
        retry_delay=0,
        cooldown_seconds=0,
    )

    result = await manager.get_candles(" eurusd ", " 15m ", limit=1)

    assert result == [candle(1)]
    first.get_candles.assert_awaited_once_with(
        symbol="EURUSD",
        timeframe="15M",
        limit=1,
    )
    second.get_candles.assert_not_awaited()


@pytest.mark.asyncio
async def test_manager_falls_back_after_provider_failure():
    first = FakeProvider("first", error=TimeoutError("timeout"))
    second = FakeProvider("second", [candle(2)])

    manager = ProviderManager(
        providers=[first, second],
        retries=0,
        retry_delay=0,
        cooldown_seconds=0,
    )

    result = await manager.get_candles("EURUSD", "15m", limit=1)

    assert result == [candle(2)]
    first.get_candles.assert_awaited_once()
    second.get_candles.assert_awaited_once()
    assert manager.last_failures[0].provider == "first"
    assert manager.last_failures[0].error_type == "TimeoutError"


@pytest.mark.asyncio
async def test_manager_retries_before_fallback():
    first = FakeProvider("first")
    first.get_candles.side_effect = [TimeoutError("temporary"), [candle(1)]]
    second = FakeProvider("second", [candle(2)])

    manager = ProviderManager(
        providers=[first, second],
        retries=1,
        retry_delay=0,
        cooldown_seconds=0,
    )

    result = await manager.get_candles("EURUSD", "15m", limit=1)

    assert result == [candle(1)]
    assert first.get_candles.await_count == 2
    second.get_candles.assert_not_awaited()
    assert len(manager.last_failures) == 1


@pytest.mark.asyncio
async def test_manager_rejects_invalid_provider_result_and_falls_back():
    first = FakeProvider("first", ["not-a-candle"])
    second = FakeProvider("second", [candle(2)])

    manager = ProviderManager(
        providers=[first, second],
        retries=0,
        retry_delay=0,
        cooldown_seconds=0,
    )

    result = await manager.get_candles("EURUSD", "15m", limit=1)

    assert result == [candle(2)]
    first.get_candles.assert_awaited_once()
    second.get_candles.assert_awaited_once()
    assert manager.last_failures[0].error_type == "ApplicationError"


@pytest.mark.asyncio
async def test_manager_raises_application_error_when_all_providers_fail():
    first = FakeProvider("first", error=TimeoutError("first timeout"))
    second = FakeProvider("second", error=ConnectionError("second down"))

    manager = ProviderManager(
        providers=[first, second],
        retries=0,
        retry_delay=0,
        cooldown_seconds=0,
    )

    with pytest.raises(ApplicationError) as exc_info:
        await manager.get_candles("EURUSD", "15m", limit=5)

    assert exc_info.value.details["symbol"] == "EURUSD"
    assert exc_info.value.details["timeframe"] == "15M"
    assert exc_info.value.details["limit"] == 5
    assert exc_info.value.details["attempted_providers"] == 2
    assert [item["provider"] for item in exc_info.value.details["failures"]] == [
        "first",
        "second",
    ]


@pytest.mark.asyncio
async def test_manager_skips_provider_in_cooldown():
    first = FakeProvider("first", error=TimeoutError("down"))
    second = FakeProvider("second", [candle(2)])

    manager = ProviderManager(
        providers=[first, second],
        retries=0,
        retry_delay=0,
        cooldown_seconds=60,
    )

    await manager.get_candles("EURUSD", "15m", limit=1)
    first.get_candles.reset_mock()
    second.get_candles.reset_mock()

    result = await manager.get_candles("EURUSD", "15m", limit=1)

    assert result == [candle(2)]
    first.get_candles.assert_not_awaited()
    second.get_candles.assert_awaited_once()
    assert manager.status()["cooldowns"]["first"] > 0


def test_manager_rejects_empty_provider_configuration():
    with pytest.raises(ValueError):
        ProviderManager(providers=[])


def test_manager_rejects_unknown_provider_name():
    with pytest.raises(ApplicationError) as exc_info:
        ProviderManager(providers=["definitely-unknown-provider"])

    assert exc_info.value.details["provider"] == "definitely-unknown-provider"
