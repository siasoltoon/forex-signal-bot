from __future__ import annotations

import pytest

from analysis.indicators import (
    ema,
    sma,
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
        None,
        None,
        2.0,
        3.0,
        4.0,
    ]


def test_ema_length() -> None:

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

    assert len(result) == 5


def test_invalid_period() -> None:

    with pytest.raises(
        ValueError,
        match="period must be greater than zero",
    ):
        sma(
            [1, 2, 3],
            0,
        )


def test_empty_values() -> None:

    with pytest.raises(
        ValueError,
        match="values cannot be empty",
    ):
        sma(
            [],
            3,
        )
