from __future__ import annotations

import pytest

from analysis.indicators.base import Indicator


class DummyIndicator(Indicator):
    """
    Fake indicator for testing base behavior.
    """

    name = "dummy"

    def calculate(
        self,
        values: list[float],
    ) -> list[float]:

        return values


def test_indicator_name() -> None:
    indicator = DummyIndicator()

    assert indicator.name == "dummy"


def test_indicator_calculate() -> None:
    indicator = DummyIndicator()

    result = indicator.calculate(
        [
            1.0,
            2.0,
            3.0,
        ]
    )

    assert result == [
        1.0,
        2.0,
        3.0,
    ]


def test_indicator_empty_values() -> None:
    indicator = DummyIndicator()

    result = indicator.calculate(
        []
    )

    assert result == []


def test_indicator_requires_implementation() -> None:
    with pytest.raises(
        TypeError
    ):
        Indicator()
