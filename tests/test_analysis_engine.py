from __future__ import annotations

import pytest

from analysis import (
    AnalysisEngine,
    AnalysisResult,
)


def test_analysis_engine_returns_result() -> None:
    engine = AnalysisEngine()

    closes = [
        1.1000,
        1.1010,
        1.1020,
        1.1030,
        1.1040,
        1.1050,
        1.1060,
        1.1070,
        1.1080,
        1.1090,
        1.1100,
        1.1110,
        1.1120,
        1.1130,
        1.1140,
        1.1150,
        1.1160,
        1.1170,
        1.1180,
        1.1190,
        1.1200,
    ]

    result = engine.analyze(
        closes
    )

    assert isinstance(
        result,
        AnalysisResult,
    )


def test_analysis_engine_detects_bullish_trend() -> None:
    engine = AnalysisEngine()

    closes = [
        float(value)
        for value in range(
            1,
            50,
        )
    ]

    result = engine.analyze(
        closes
    )

    assert result.trend == "bullish"


def test_analysis_engine_contains_indicators() -> None:
    engine = AnalysisEngine()

    closes = [
        float(value)
        for value in range(
            1,
            50,
        )
    ]

    result = engine.analyze(
        closes
    )

    assert "sma" in result.indicators

    assert "ema" in result.indicators

    assert "rsi" in result.indicators

    assert "macd" in result.indicators

    assert "stochastic_rsi" in result.indicators


def test_empty_prices_raise_error() -> None:
    engine = AnalysisEngine()

    with pytest.raises(
        ValueError
    ):
        engine.analyze(
            []
        )


def test_invalid_input_type() -> None:
    engine = AnalysisEngine()

    with pytest.raises(
        TypeError
    ):
        engine.analyze(
            "invalid"
        )
