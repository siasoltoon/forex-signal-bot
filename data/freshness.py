from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True, slots=True)
class FreshnessReport:
    """Deterministic freshness assessment for the latest market candle."""

    status: str
    age: timedelta
    max_age: timedelta

    @property
    def is_usable(self) -> bool:
        return self.status in {"FRESH", "WARNING"}


class FreshnessPolicy:
    """Classify candle freshness without depending on wall-clock time internally."""

    FRESH = "FRESH"
    WARNING = "WARNING"
    STALE = "STALE"
    REJECT = "REJECT"

    @staticmethod
    def _validate_timestamp(timestamp: datetime) -> None:
        if not isinstance(timestamp, datetime):
            raise TypeError("timestamp must be a datetime.")
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware.")

    @staticmethod
    def _validate_duration(value: timedelta, name: str) -> None:
        if not isinstance(value, timedelta):
            raise TypeError(f"{name} must be a timedelta.")
        if value <= timedelta(0):
            raise ValueError(f"{name} must be greater than zero.")

    @classmethod
    def assess(
        cls,
        timestamp: datetime,
        *,
        now: datetime,
        timeframe: timedelta,
        warning_after: timedelta | None = None,
        stale_after: timedelta | None = None,
        reject_after: timedelta | None = None,
    ) -> FreshnessReport:
        """Assess freshness using an explicit reference time for deterministic tests."""
        cls._validate_timestamp(timestamp)
        cls._validate_timestamp(now)
        cls._validate_duration(timeframe, "timeframe")

        warning = warning_after or timeframe * 2
        stale = stale_after or timeframe * 3
        reject = reject_after or timeframe * 6

        for value, name in (
            (warning, "warning_after"),
            (stale, "stale_after"),
            (reject, "reject_after"),
        ):
            cls._validate_duration(value, name)

        if not warning <= stale <= reject:
            raise ValueError("freshness thresholds must satisfy warning <= stale <= reject.")

        reference = now.astimezone(timezone.utc)
        candle_time = timestamp.astimezone(timezone.utc)
        age = reference - candle_time

        if age < timedelta(0):
            raise ValueError("timestamp cannot be in the future.")

        # Thresholds are inclusive at the upper edge of each state. This makes
        # the boundary deterministic: warning_after itself is WARNING, while
        # stale_after itself remains WARNING and reject_after itself remains STALE.
        if age < warning:
            status = cls.FRESH
        elif age <= stale:
            status = cls.WARNING
        elif age <= reject:
            status = cls.STALE
        else:
            status = cls.REJECT

        return FreshnessReport(status=status, age=age, max_age=reject)


__all__ = ["FreshnessPolicy", "FreshnessReport"]
