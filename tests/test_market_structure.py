from __future__ import annotations

import pytest

from analysis.market_structure import (
    MarketStructureDetector,
    MarketStructureResult,
    SwingPoint,
)


def test_market_structure_returns_result() -> None:
    detector = MarketStructureDetector()

    prices = [
        1.0,
        1.2,
        1.1,
        1.4,
        1.3,
        1.6,
        1.5,
    ]

    result = detector.analyze(
        prices
    )

    assert isinstance(
        result,
        MarketStructureResult,
    )


def test_detects_swings() -> None:
    detector = MarketStructureDetector()

    prices = [
        1.0,
        1.5,
        1.0,
        1.8,
        1.2,
    ]

    result = detector.analyze(
        prices
    )

    assert len(
        result.swings
    ) > 0

    assert isinstance(
        result.swings[0],
        SwingPoint,
    )


def test_bullish_structure() -> None:
    detector = MarketStructureDetector()

    prices = [
        1.0,
        1.5,
        1.2,
        2.0,
        1.7,
        2.5,
    ]

    result = detector.analyze(
        prices
    )

    assert result.trend == "bullish"



def test_bearish_structure() -> None:
    detector = MarketStructureDetector()

    prices = [
        2.5,
        2.0,
        2.2,
        1.7,
        1.9,
        1.3,
    ]

    result = detector.analyze(
        prices
    )

    assert result.trend == "bearish"



def test_invalid_prices_type() -> None:
    detector = MarketStructureDetector()

    with pytest.raises(
        TypeError
    ):
        detector.analyze(
            "invalid"
        )



def test_not_enough_prices() -> None:
    detector = MarketStructureDetector()

    with pytest.raises(
        ValueError
    ):
        detector.analyze(
            [
                1.0,
                1.1,
            ]
        )
