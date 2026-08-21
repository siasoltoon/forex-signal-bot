from __future__ import annotations

from datetime import datetime, timezone

import pytest

from data.models import Candle


def create_candle() -> Candle:
    return Candle(
        symbol="EUR_USD",
        timestamp=datetime(
            2026,
            1,
            1,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        open=1.1000,
        high=1.1200,
        low=1.0900,
        close=1.1100,
        volume=500,
    )


def test_candle_creation() -> None:
    candle = create_candle()

    assert candle.symbol == "EUR_USD"
    assert candle.open == 1.1000
    assert candle.high == 1.1200
    assert candle.low == 1.0900
    assert candle.close == 1.1100
    assert candle.volume == 500


def test_candle_timestamp() -> None:
    candle = create_candle()

    assert isinstance(
        candle.timestamp,
        datetime,
    )

    assert candle.timestamp.tzinfo == timezone.utc


def test_typical_price() -> None:
    candle = create_candle()

    result = candle.typical_price

    expected = (
        1.1200
        + 1.0900
        + 1.1100
    ) / 3

    assert result == expected


def test_candle_is_immutable() -> None:
    candle = create_candle()

    with pytest.raises(
        AttributeError
    ):
        candle.close = 1.2000


def test_candle_equality() -> None:
    first = create_candle()
    second = create_candle()

    assert first == second


def test_candle_different_values() -> None:
    first = create_candle()

    second = Candle(
        symbol="GBP_USD",
        timestamp=first.timestamp,
        open=1.1000,
        high=1.1200,
        low=1.0900,
        close=1.1100,
        volume=500,
    )

    assert first != second
