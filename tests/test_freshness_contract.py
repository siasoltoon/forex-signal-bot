from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from data.freshness import FreshnessPolicy


NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
INTERVAL = timedelta(minutes=15)


def ts(minutes_ago: int) -> datetime:
    return NOW - timedelta(minutes=minutes_ago)


def test_fresh_data_is_usable():
    report = FreshnessPolicy.assess(
        ts(10), now=NOW, timeframe=INTERVAL
    )

    assert report.status == FreshnessPolicy.FRESH
    assert report.is_usable is True
    assert report.age == timedelta(minutes=10)


def test_warning_data_remains_usable_but_is_flagged():
    report = FreshnessPolicy.assess(
        ts(35), now=NOW, timeframe=INTERVAL
    )

    assert report.status == FreshnessPolicy.WARNING
    assert report.is_usable is True


def test_stale_data_is_not_usable():
    report = FreshnessPolicy.assess(
        ts(50), now=NOW, timeframe=INTERVAL
    )

    assert report.status == FreshnessPolicy.STALE
    assert report.is_usable is False


def test_rejected_data_is_not_usable():
    report = FreshnessPolicy.assess(
        ts(100), now=NOW, timeframe=INTERVAL
    )

    assert report.status == FreshnessPolicy.REJECT
    assert report.is_usable is False


def test_exact_thresholds_are_deterministic():
    assert FreshnessPolicy.assess(
        ts(30), now=NOW, timeframe=INTERVAL
    ).status == FreshnessPolicy.WARNING
    assert FreshnessPolicy.assess(
        ts(45), now=NOW, timeframe=INTERVAL
    ).status == FreshnessPolicy.WARNING
    assert FreshnessPolicy.assess(
        ts(46), now=NOW, timeframe=INTERVAL
    ).status == FreshnessPolicy.STALE
    assert FreshnessPolicy.assess(
        ts(90), now=NOW, timeframe=INTERVAL
    ).status == FreshnessPolicy.STALE
    assert FreshnessPolicy.assess(
        ts(91), now=NOW, timeframe=INTERVAL
    ).status == FreshnessPolicy.REJECT


def test_custom_thresholds_are_supported():
    report = FreshnessPolicy.assess(
        ts(8),
        now=NOW,
        timeframe=INTERVAL,
        warning_after=timedelta(minutes=5),
        stale_after=timedelta(minutes=10),
        reject_after=timedelta(minutes=20),
    )

    assert report.status == FreshnessPolicy.WARNING
    assert report.max_age == timedelta(minutes=20)


def test_future_candle_is_rejected():
    with pytest.raises(ValueError, match="future"):
        FreshnessPolicy.assess(
            NOW + timedelta(minutes=1),
            now=NOW,
            timeframe=INTERVAL,
        )


def test_naive_timestamp_is_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        FreshnessPolicy.assess(
            datetime(2026, 1, 1, 11, 50),
            now=NOW,
            timeframe=INTERVAL,
        )


def test_naive_now_is_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        FreshnessPolicy.assess(
            ts(5),
            now=datetime(2026, 1, 1, 12, 0),
            timeframe=INTERVAL,
        )


def test_invalid_timeframe_and_thresholds_are_rejected():
    with pytest.raises(TypeError, match="timeframe"):
        FreshnessPolicy.assess(ts(5), now=NOW, timeframe="15m")

    with pytest.raises(ValueError, match="timeframe"):
        FreshnessPolicy.assess(ts(5), now=NOW, timeframe=timedelta(0))

    with pytest.raises(ValueError, match="thresholds"):
        FreshnessPolicy.assess(
            ts(5),
            now=NOW,
            timeframe=INTERVAL,
            warning_after=timedelta(minutes=30),
            stale_after=timedelta(minutes=10),
            reject_after=timedelta(minutes=60),
        )


def test_timezone_offsets_are_normalized_to_utc():
    timestamp = datetime(
        2026, 1, 1, 15, 0,
        tzinfo=timezone(timedelta(hours=3)),
    )

    report = FreshnessPolicy.assess(
        timestamp,
        now=NOW,
        timeframe=INTERVAL,
    )

    assert report.age == timedelta(0)
    assert report.status == FreshnessPolicy.FRESH
