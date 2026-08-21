from __future__ import annotations

import pytest

from analysis import (
    FullAnalysisEngine,
    AnalysisReport,
)



def test_full_engine_returns_report() -> None:

    engine = FullAnalysisEngine()

    closes = [
        1.1000,
        1.1010,
        1.0990,
        1.1030,
        1.1010,
        1.1060,
        1.1040,
        1.1080,
    ]


    result = engine.analyze(
        closes
    )


    assert isinstance(
        result,
        AnalysisReport,
    )


    assert result.trend in [
        "bullish",
        "bearish",
        "unknown",
    ]



def test_full_engine_has_signal() -> None:

    engine = FullAnalysisEngine()


    result = engine.analyze(
        [
            1.0,
            1.2,
            1.1,
            1.4,
            1.3,
            1.6,
        ]
    )


    assert result.signal in [
        "BUY",
        "SELL",
        "NEUTRAL",
    ]



def test_full_engine_confidence_range() -> None:

    engine = FullAnalysisEngine()


    result = engine.analyze(
        [
            1.0,
            1.2,
            1.1,
            1.5,
            1.3,
            1.7,
        ]
    )


    assert 0 <= result.confidence <= 1



def test_full_engine_invalid_input() -> None:

    engine = FullAnalysisEngine()


    with pytest.raises(
        ValueError
    ):
        engine.analyze(
            [
                1.0,
                1.1,
            ]
        )
