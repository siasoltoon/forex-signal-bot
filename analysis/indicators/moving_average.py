from __future__ import annotations

from collections.abc import Sequence

from core.errors import ApplicationError


def _validate_period(
    period: int,
) -> None:
    if not isinstance(
        period,
        int,
    ):
        raise TypeError(
            "period must be an integer."
        )

    if period < 1:
        raise ValueError(
            "period must be greater than zero."
        )


def _validate_values(
    values: Sequence[float],
) -> None:
    if not isinstance(
        values,
        Sequence,
    ):
        raise TypeError(
            "values must be a sequence."
        )

    if len(values) == 0:
        raise ValueError(
            "values cannot be empty."
        )


def sma(
    values: Sequence[float],
    period: int,
) -> list[float | None]:
    """
    Simple Moving Average.

    Returns a list with None values
    until enough data is available.
    """

    _validate_period(period)
    _validate_values(values)

    result: list[float | None] = []

    window_sum = 0.0

    for index, value in enumerate(values):

        window_sum += float(value)

        if index >= period:
            window_sum -= float(
                values[index - period]
            )

        if index < period - 1:
            result.append(None)

        else:
            result.append(
                window_sum / period
            )

    return result


def ema(
    values: Sequence[float],
    period: int,
) -> list[float | None]:
    """
    Exponential Moving Average.
    """

    _validate_period(period)
    _validate_values(values)

    multiplier = (
        2 / (period + 1)
    )

    result: list[float | None] = []

    ema_value: float | None = None

    for index, value in enumerate(values):

        price = float(value)

        if index < period - 1:
            result.append(None)
            continue

        if ema_value is None:

            initial = sum(
                float(item)
                for item in values[
                    index - period + 1:
                    index + 1
                ]
            ) / period

            ema_value = initial

        else:
            ema_value = (
                (
                    price - ema_value
                )
                * multiplier
            ) + ema_value

        result.append(
            ema_value
        )

    return result
