from __future__ import annotations

import numpy as np

from analysis.indicators.base import validate_series


def true_range(
    highs: list[float],
    lows: list[float],
    closes: list[float],
) -> list[float]:
    """
    Calculate True Range values.
    """

    validate_series(highs)
    validate_series(lows)
    validate_series(closes)

    if not (
        len(highs)
        == len(lows)
        == len(closes)
    ):
        raise ValueError(
            "Input series must have equal length."
        )

    result: list[float] = []

    for index in range(len(highs)):
        if index == 0:
            tr = highs[index] - lows[index]
        else:
            tr = max(
                highs[index] - lows[index],
                abs(
                    highs[index]
                    - closes[index - 1]
                ),
                abs(
                    lows[index]
                    - closes[index - 1]
                ),
            )

        result.append(float(tr))

    return result


def atr(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    period: int = 14,
) -> list[float]:
    """
    Average True Range.
    """

    if period < 1:
        raise ValueError(
            "period must be greater than zero."
        )

    ranges = true_range(
        highs,
        lows,
        closes,
    )

    if len(ranges) < period:
        return []

    values: list[float] = []

    for index in range(
        period - 1,
        len(ranges),
    ):
        window = ranges[
            index - period + 1 :
            index + 1
        ]

        values.append(
            float(
                np.mean(window)
            )
        )

    return values


def bollinger_bands(
    prices: list[float],
    period: int = 20,
    std_multiplier: float = 2.0,
) -> tuple[
    list[float],
    list[float],
    list[float],
]:
    """
    Calculate Bollinger Bands.

    Returns:
        upper_band,
        middle_band,
        lower_band
    """

    validate_series(prices)

    if period < 1:
        raise ValueError(
            "period must be greater than zero."
        )

    if std_multiplier <= 0:
        raise ValueError(
            "std_multiplier must be positive."
        )

    if len(prices) < period:
        return (
            [],
            [],
            [],
        )

    upper: list[float] = []
    middle: list[float] = []
    lower: list[float] = []

    for index in range(
        period - 1,
        len(prices),
    ):
        window = prices[
            index - period + 1 :
            index + 1
        ]

        mean = float(
            np.mean(window)
        )

        deviation = float(
            np.std(window)
        )

        middle.append(mean)

        upper.append(
            mean
            + (
                deviation
                * std_multiplier
            )
        )

        lower.append(
            mean
            - (
                deviation
                * std_multiplier
            )
        )

    return (
        upper,
        middle,
        lower,
    )


def standard_deviation(
    prices: list[float],
    period: int = 20,
) -> list[float]:
    """
    Rolling standard deviation.
    """

    validate_series(prices)

    if period < 1:
        raise ValueError(
            "period must be greater than zero."
        )

    if len(prices) < period:
        return []

    result: list[float] = []

    for index in range(
        period - 1,
        len(prices),
    ):
        window = prices[
            index - period + 1 :
            index + 1
        ]

        result.append(
            float(
                np.std(window)
            )
        )

    return result
