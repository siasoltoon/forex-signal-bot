from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from data.models import Candle
from data.quality import DataQuality


BASE = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def make_candle(
    minute: int = 0,
    *,
    symbol: str = "EURUSD",
    close: float = 1.1005,
) -> Candle:
    return Candle(
        symbol=symbol,
        timestamp=BASE + timedelta(minutes=minute),
        open=1.1000,
        high=max(1.1010, close),
        low=min(1.0990, close),
        close=close,
        volume=100.0,
    )


def test_valid_sequence_is_fresh_structurally_and_has_no_quality_issues():
    candles = [make_candle(0), make_candle(1), make_candle(2)]

    report = DataQuality.inspect(
        candles,
        expected_symbol="EURUSD",
        expected_interval=timedelta(minutes=1),
    )

    assert report.valid is True
    assert report.candle_count == 3
    assert report.duplicate_timestamps == 0
    assert report.out_of_order == 0
    assert report.gaps == 0
    assert report.suspicious_gaps == 0
    assert report.issues == ()


def test_duplicate_timestamps_are_rejected():
    candles = [make_candle(0), make_candle(1), make_candle(1)]

    report = DataQuality.inspect(candles, expected_symbol="EURUSD")

    assert report.valid is False
    assert report.duplicate_timestamps == 1
    assert report.out_of_order == 1
    assert any("duplicate timestamp" in issue for issue in report.issues)

    with pytest.raises(ValueError, match="Invalid market data"):
        DataQuality.validate(candles, expected_symbol="EURUSD")


def test_out_of_order_candles_are_rejected():
    candles = [make_candle(0), make_candle(2), make_candle(1)]

    report = DataQuality.inspect(candles, expected_symbol="EURUSD")

    assert report.valid is False
    assert report.out_of_order == 1
    assert any("timestamp order violation" in issue for issue in report.issues)


def test_large_gap_is_detected_when_expected_interval_is_known():
    candles = [make_candle(0), make_candle(1), make_candle(5)]

    report = DataQuality.inspect(
        candles,
        expected_symbol="EURUSD",
        expected_interval=timedelta(minutes=1),
        gap_tolerance=1,
    )

    assert report.valid is False
    assert report.gaps == 1
    assert report.suspicious_gaps == 1
    assert any("gap detected" in issue for issue in report.issues)


def test_gap_tolerance_allows_expected_small_gap():
    candles = [make_candle(0), make_candle(1), make_candle(3)]

    report = DataQuality.inspect(
        candles,
        expected_symbol="EURUSD",
        expected_interval=timedelta(minutes=1),
        gap_tolerance=2,
    )

    assert report.valid is True
    assert report.gaps == 0


def test_wrong_symbol_is_rejected():
    candles = [make_candle(0), make_candle(1, symbol="GBPUSD")]

    report = DataQuality.inspect(candles, expected_symbol="EURUSD")

    assert report.valid is False
    assert any("unexpected symbol" in issue for issue in report.issues)


def test_non_candle_item_is_reported_as_invalid():
    report = DataQuality.inspect(
        [make_candle(0), object()],
        expected_symbol="EURUSD",
    )

    assert report.valid is False
    assert report.candle_count == 2
    assert any("is not a Candle" in issue for issue in report.issues)


def test_none_and_invalid_gap_configuration_are_rejected():
    with pytest.raises(TypeError, match="candles cannot be None"):
        DataQuality.inspect(None)

    with pytest.raises(TypeError, match="gap_tolerance"):
        DataQuality.inspect([make_candle()], gap_tolerance=True)

    with pytest.raises(ValueError, match="gap_tolerance"):
        DataQuality.inspect([make_candle()], gap_tolerance=0)

    with pytest.raises(TypeError, match="interval"):
        DataQuality.inspect([make_candle()], expected_interval="1m")

    with pytest.raises(ValueError, match="interval"):
        DataQuality.inspect([make_candle()], expected_interval=timedelta(0))


def test_validate_does_not_mutate_or_repair_input():
    candles = [make_candle(0), make_candle(1)]

    result = DataQuality.validate(
        candles,
        expected_symbol="EURUSD",
        expected_interval=timedelta(minutes=1),
    )

    assert result == candles
    assert result is not candles


def test_empty_sequence_is_structurally_valid():
    report = DataQuality.inspect(
        [],
        expected_symbol="EURUSD",
        expected_interval=timedelta(minutes=1),
    )

    assert report.valid is True
    assert report.candle_count == 0
    assert report.issues == ()


def test_market_candle_model_rejects_naive_timestamp():
    with pytest.raises(ValueError, match="timezone-aware"):
        Candle(
            symbol="EURUSD",
            timestamp=datetime(2026, 1, 1, 12, 0),
            open=1.1,
            high=1.101,
            low=1.099,
            close=1.1005,
            volume=100.0,
        )
