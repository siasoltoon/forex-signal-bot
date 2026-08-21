from __future__ import annotations

import pytest

from analysis.indicators import (
    sma,
    ema,
    rsi,
    macd,
    stochastic_rsi,
)


def test_sma() -> None:
    values = [
        1,
        2,
        3,
        4,
        5,
    ]

    result = sma(
        values,
        period=3,
    )

    assert result == [
        2.0,
        3.0,
        4.0,
    ]


def test_ema() -> None:
    values = [
        1,
        2,
        3,
        4,
        5,
    ]

    result = ema(
        values,
        period=3,
    )

    assert len(result) == len(values)

    assert result[0] == 1


def test_rsi() -> None:
    values = [
        1,
        2,
        3,
        2,
        4,
        5,
        6,
    ]

    result = rsi(
        values,
        period=3,
    )

    assert len(result) == len(values)

    assert all(
        0 <= value <= 100
        for value in result
        if value is not None
    )


def test_macd() -> None:
    values = [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
    ]

    result = macd(
        values,
    )

    assert isinstance(
        result,
        tuple,
    )

    assert len(result) == 3


def test_stochastic_rsi() -> None:
    values = [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
    ]

    result = stochastic_rsi(
        values,
        period=5,
    )

    assert len(result) == len(values)


def test_empty_series() -> None:
    with pytest.raises(
        ValueError
    ):
        sma(
            [],
            period=3,
        )


def test_invalid_period() -> None:
    values = [
        1,
        2,
        3,
    ]

    with pytest.raises(
        ValueError
    ):
        sma(
            values,
            period=0,
        )


def test_period_larger_than_series() -> None:
    values = [
        1,
        2,
    ]

    result = sma(
        values,
        period=5,
    )

    assert result == []


def test_non_numeric_values() -> None:
    values = [
        1,
        "bad",
        3,
    ]

    with pytest.raises(
        TypeError
    ):
        sma(
            values,
            period=2,
        )
