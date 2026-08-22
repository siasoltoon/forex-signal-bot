from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from analysis import (
    FullAnalysisEngine,
    AnalysisReport,
)
from data.models import Candle


def make_candles(closes: list[float]) -> list[Candle]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    candles: list[Candle] = []

    for index, close in enumerate(closes):
        previous_close = (
            closes[index - 1]
            if index > 0
            else close
        )
        open_price = previous_close
        high = max(open_price, close) * 1.001
        low = min(open_price, close) * 0.999

        candles.append(
            Candle(
                symbol="EUR_USD",
                timestamp=start + timedelta(minutes=15 * index),
                open=open_price,
                high=high,
                low=low,
                close=close,
                volume=100.0,
            )
        )

    return candles


def test_full_engine_returns_report() -> None:
    engine = FullAnalysisEngine()

    result = engine.analyze(
        make_candles(
            [
                1.1000,
                1.1010,
                1.0990,
                1.1030,
                1.1010,
                1.1060,
                1.1040,
                1.1080,
            ]
        )
    )

    assert isinstance(result, AnalysisReport)
    assert result.trend in [
        "bullish",
        "bearish",
        "unknown",
    ]


def test_full_engine_has_signal() -> None:
    engine = FullAnalysisEngine()

    result = engine.analyze(
        make_candles(
            [
                1.0,
                1.2,
                1.1,
                1.4,
                1.3,
                1.6,
            ]
        )
    )

    assert result.signal in [
        "BUY",
        "SELL",
        "NEUTRAL",
    ]


def test_full_engine_confidence_range() -> None:
    engine = FullAnalysisEngine()

    result = engine.analyze(
        make_candles(
            [
                1.0,
                1.2,
                1.1,
                1.5,
                1.3,
                1.7,
            ]
        )
    )

    assert 0 <= result.confidence <= 1


def test_full_engine_invalid_input() -> None:
    engine = FullAnalysisEngine()

    with pytest.raises(ValueError):
        engine.analyze([])


def test_full_engine_uses_canonical_candle_model() -> None:
    engine = FullAnalysisEngine()
    candles = make_candles(
        [
            1.0,
            1.1,
            1.05,
            1.2,
            1.15,
            1.3,
        ]
    )

    result = engine.analyze(candles)

    assert result is not None
    assert all(
        isinstance(candle, Candle)
        for candle in candles
    )
    assert candles[0].symbol == "EUR_USD"
    assert candles[0].timestamp.tzinfo is not None
