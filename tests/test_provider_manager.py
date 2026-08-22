from __future__ import annotations

from datetime import datetime, timezone

import pytest

from data.models import Candle
from data.provider_manager import ProviderManager


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
    Create a deterministic Candle for ProviderManager tests.

    The production Candle model requires timestamp to be a datetime.
    Integer timestamps are converted to UTC datetimes here so the
    tests remain simple and deterministic.
    """

    return Candle(
        symbol=symbol,
        timestamp=datetime.fromtimestamp(
            timestamp,
            tz=timezone.utc,
        ),
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=volume,
    )


class FakeProvider:
    """
    Simple async provider used by ProviderManager tests.
    """

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
    ):
        self.calls += 1

        if not self.responses:
            return []

        response = self.responses.pop(0)

        if isinstance(response, Exception):
            raise response

        return response


@pytest.mark.asyncio
async def test_manager_uses_first_provider(
    monkeypatch,
) -> None:
    candles = [
        make_candle(1),
        make_candle(2),
        make_candle(3),
    ]

    first = FakeProvider([candles])
    second = FakeProvider([[]])

    manager = ProviderManager(
        providers=[
            first,
            second,
        ],
    )

    result = await manager.get_candles(
        symbol="EUR_USD",
        timeframe="M15",
        limit=10,
    )

    assert result == candles
    assert first.calls == 1
    assert second.calls == 0


@pytest.mark.asyncio
async def test_manager_retries_failed_provider(
    monkeypatch,
) -> None:
    candles = [
        make_candle(1),
    ]

    first = FakeProvider(
        [
            RuntimeError("temporary failure"),
            candles,
        ]
    )

    manager = ProviderManager(
        providers=[first],
    )

    result = await manager.get_candles(
        symbol="EUR_USD",
        timeframe="M15",
        limit=10,
    )

    assert result == candles
    assert first.calls == 2


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
            RuntimeError("provider unavailable"),
            RuntimeError("provider unavailable"),
            RuntimeError("provider unavailable"),
        ]
    )

    second = FakeProvider(
        [
            candles,
        ]
    )

    manager = ProviderManager(
        providers=[
            first,
            second,
        ],
    )

    result = await manager.get_candles(
        symbol="EUR_USD",
        timeframe="M15",
        limit=10,
    )

    assert result == candles

    assert first.calls >= 1
    assert second.calls == 1


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

    manager = ProviderManager(
        providers=[
            first,
            second,
        ],
    )

    result = await manager.get_candles(
        symbol="EUR_USD",
        timeframe="M15",
        limit=10,
    )

    assert result == second_candles
    assert second.calls == 1


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
        [
            candles,
        ]
    )

    manager = ProviderManager(
        providers=[provider],
    )

    result = await manager.get_candles(
        symbol="EUR_USD",
        timeframe="M15",
        limit=10,
    )

    assert [
        int(candle.timestamp.timestamp())
        for candle in result
    ] == [
        1,
        2,
        3,
    ]


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
        [
            candles,
        ]
    )

    manager = ProviderManager(
        providers=[provider],
    )

    result = await manager.get_candles(
        symbol="EUR_USD",
        timeframe="M15",
        limit=10,
    )

    timestamps = [
        int(candle.timestamp.timestamp())
        for candle in result
    ]

    assert timestamps == [
        1,
        2,
        3,
    ]


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
        [
            candles,
        ]
    )

    manager = ProviderManager(
        providers=[provider],
    )

    result = await manager.get_candles(
        symbol="EUR_USD",
        timeframe="M15",
        limit=3,
    )

    assert len(result) == 3

    assert [
        int(candle.timestamp.timestamp())
        for candle in result
    ] == [
        3,
        4,
        5,
    ]
