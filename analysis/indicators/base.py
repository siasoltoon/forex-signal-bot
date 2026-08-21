from __future__ import annotations


def validate_series(
    values: list[float],
) -> None:
    """
    Validate indicator input series.
    """

    if not isinstance(
        values,
        list,
    ):
        raise TypeError(
            "values must be a list."
        )

    if len(values) == 0:
        raise ValueError(
            "values cannot be empty."
        )

    for value in values:
        if not isinstance(
            value,
            (int, float),
        ):
            raise TypeError(
                "series values must be numeric."
            )


def validate_period(
    period: int,
) -> None:
    """
    Validate indicator period.
    """

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
