from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from data.models import Candle
from data.quality import DataQuality


def candle(index: int, *, symbol: str = "EUR_USD") -> Candle:
    return Candle(
        symbol=symbol,
        timestamp=datetime(2026, 1, 1, 12, index, tzinfo=timezone.utc),
        open=1.10,
        high=1.12,
        low=1.09,
        close=1.11,
        volume=100,
    )


def test_quality_accepts_clean_series() -> None:
    candles = [candle(0), candle(1), candle(2)]
    report = DataQuality.inspect(
        candles,
        expected_symbol="EUR_USD",
        expected_interval=timedelta(minutes=1),
    )
    assert report.valid
    assert report.gaps == 0
    assert report.duplicate_timestamps == 0


def test_quality_detects_duplicate_timestamp() -> None:
    candles = [candle(0), candle(1), candle(1)]
    report = DataQuality.inspect(candles)
    assert not report.valid
    assert report.duplicate_timestamps == 1


def test_quality_detects_out_of_order_data() -> None:
    candles = [candle(1), candle(0)]
    report = DataQuality.inspect(candles)
    assert not report.valid
    assert report.out_of_order == 1


def test_quality_detects_symbol_mismatch() -> None:
    report = DataQuality.inspect(
        [candle(0, symbol="GBP_USD")],
        expected_symbol="EUR_USD",
    )
    assert not report.valid


def test_quality_detects_gap() -> None:
    candles = [candle(0), candle(3)]
    report = DataQuality.inspect(
        candles,
        expected_interval=timedelta(minutes=1),
    )
    assert not report.valid
    assert report.gaps == 1


def test_quality_validate_raises_for_invalid_data() -> None:
    with pytest.raises(ValueError):
        DataQuality.validate(
            [candle(0), candle(0)],
        )
