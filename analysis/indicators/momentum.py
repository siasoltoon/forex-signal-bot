from __future__ import annotations

from collections.abc import Sequence


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


def rsi(
    values: Sequence[float],
    period: int = 14,
) -> list[float | None]:
    """
    Relative Strength Index.
    """

    _validate_period(period)
    _validate_values(values)

    result: list[float | None] = [
        None
    ] * len(values)

    gains: list[float] = []
    losses: list[float] = []

    for index in range(1, len(values)):

        change = (
            float(values[index])
            -
            float(values[index - 1])
        )

        if change >= 0:
            gains.append(change)
            losses.append(0.0)

        else:
            gains.append(0.0)
            losses.append(abs(change))

    if len(values) <= period:
        return result

    avg_gain = (
        sum(gains[:period])
        /
        period
    )

    avg_loss = (
        sum(losses[:period])
        /
        period
    )

    if avg_loss == 0:
        result[period] = 100.0

    else:
        rs = avg_gain / avg_loss
        result[period] = (
            100
            -
            (
                100
                /
                (1 + rs)
            )
        )

    for index in range(
        period + 1,
        len(values),
    ):

        gain = gains[index - 1]
        loss = losses[index - 1]

        avg_gain = (
            (
                avg_gain
                *
                (period - 1)
            )
            +
            gain
        ) / period

        avg_loss = (
            (
                avg_loss
                *
                (period - 1)
            )
            +
            loss
        ) / period

        if avg_loss == 0:
            result[index] = 100.0

        else:
            rs = avg_gain / avg_loss

            result[index] = (
                100
                -
                (
                    100
                    /
                    (1 + rs)
                )
            )

    return result


def macd(
    values: Sequence[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> dict[str, list[float | None]]:
    """
    Moving Average Convergence Divergence.
    """

    from analysis.indicators.moving_average import ema

    _validate_values(values)

    if fast >= slow:
        raise ValueError(
            "fast period must be smaller than slow period."
        )

    fast_line = ema(
        values,
        fast,
    )

    slow_line = ema(
        values,
        slow,
    )

    macd_line: list[float | None] = []

    for fast_value, slow_value in zip(
        fast_line,
        slow_line,
    ):
        if (
            fast_value is None
            or
            slow_value is None
        ):
            macd_line.append(None)

        else:
            macd_line.append(
                fast_value - slow_value
            )

    valid_macd = [
        value
        for value in macd_line
        if value is not None
    ]

    signal_line = ema(
        valid_macd,
        signal,
    )

    return {
        "macd": macd_line,
        "signal": signal_line,
    }


def stochastic_rsi(
    values: Sequence[float],
    rsi_period: int = 14,
    stoch_period: int = 14,
) -> list[float | None]:
    """
    Stochastic RSI.
    """

    _validate_period(rsi_period)
    _validate_period(stoch_period)
    _validate_values(values)

    rsi_values = rsi(
        values,
        rsi_period,
    )

    result: list[float | None] = [
        None
    ] * len(values)

    for index in range(
        len(values)
    ):

        if index < (
            rsi_period
            +
            stoch_period
        ):
            continue

        window = [
            value
            for value in rsi_values[
                index - stoch_period + 1:
                index + 1
            ]
            if value is not None
        ]

        if len(window) != stoch_period:
            continue

        minimum = min(window)
        maximum = max(window)

        if maximum == minimum:
            result[index] = 0.0

        else:
            result[index] = (
                (
                    rsi_values[index]
                    -
                    minimum
                )
                /
                (
                    maximum
                    -
                    minimum
                )
            )

    return result
