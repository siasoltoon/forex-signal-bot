from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from math import isfinite
from typing import Any, Iterable, Mapping


def _validate_timezone_aware(value: datetime, field_name: str) -> None:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime.")

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware.")


def _validate_finite(value: float, field_name: str) -> None:
    try:
        numeric_value = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{field_name} must be numeric.") from exc

    if not isfinite(numeric_value):
        raise ValueError(f"{field_name} must be finite.")


@dataclass(frozen=True, slots=True)
class OHLCV:
    """
    Canonical OHLCV market candle representation.

    This is the lightweight domain representation used by:
        - market data
        - technical analysis
        - price action
        - signal engine
        - risk engine
        - AI analysis

    Provider-specific models must be converted into this model
    before entering the analysis/domain layer.
    """

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    def __post_init__(self) -> None:
        _validate_timezone_aware(self.timestamp, "timestamp")

        for name, value in (
            ("open", self.open),
            ("high", self.high),
            ("low", self.low),
            ("close", self.close),
            ("volume", self.volume),
        ):
            _validate_finite(value, name)

        if self.open <= 0:
            raise ValueError("open must be greater than zero.")

        if self.high <= 0:
            raise ValueError("high must be greater than zero.")

        if self.low <= 0:
            raise ValueError("low must be greater than zero.")

        if self.close <= 0:
            raise ValueError("close must be greater than zero.")

        if self.volume < 0:
            raise ValueError("volume cannot be negative.")

        if self.high < self.low:
            raise ValueError("high cannot be lower than low.")

        if self.high < max(self.open, self.close):
            raise ValueError(
                "high must be greater than or equal to open and close."
            )

        if self.low > min(self.open, self.close):
            raise ValueError(
                "low must be less than or equal to open and close."
            )

    @property
    def typical_price(self) -> float:
        """Return the typical price: (H + L + C) / 3."""
        return (self.high + self.low + self.close) / 3.0

    @property
    def range(self) -> float:
        """Return the full candle range."""
        return self.high - self.low

    @property
    def spread(self) -> float:
        """Backward-compatible alias for candle range."""
        return self.range

    @property
    def body(self) -> float:
        """Return the absolute candle body size."""
        return abs(self.close - self.open)

    @property
    def body_high(self) -> float:
        """Return the upper body boundary."""
        return max(self.open, self.close)

    @property
    def body_low(self) -> float:
        """Return the lower body boundary."""
        return min(self.open, self.close)

    @property
    def upper_wick(self) -> float:
        """Return the upper wick size."""
        return self.high - self.body_high

    @property
    def lower_wick(self) -> float:
        """Return the lower wick size."""
        return self.body_low - self.low

    @property
    def is_bullish(self) -> bool:
        """Return True when close is above open."""
        return self.close > self.open

    @property
    def is_bearish(self) -> bool:
        """Return True when close is below open."""
        return self.close < self.open

    @property
    def is_doji(self) -> bool:
        """Return True when open and close are equal."""
        return self.close == self.open

    @property
    def midpoint(self) -> float:
        """Return the midpoint between high and low."""
        return (self.high + self.low) / 2.0

    @property
    def body_ratio(self) -> float:
        """
        Return body size relative to total candle range.

        Returns 0.0 for a zero-range candle.
        """
        if self.range == 0:
            return 0.0

        return self.body / self.range

    @property
    def upper_wick_ratio(self) -> float:
        """Return upper wick relative to total candle range."""
        if self.range == 0:
            return 0.0

        return self.upper_wick / self.range

    @property
    def lower_wick_ratio(self) -> float:
        """Return lower wick relative to total candle range."""
        if self.range == 0:
            return 0.0

        return self.lower_wick / self.range


@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    """
    Immutable market snapshot.

    Represents a coherent set of candles for one symbol/timeframe.
    """

    symbol: str
    timeframe: str
    candles: tuple[OHLCV, ...]
    timestamp: datetime
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.symbol, str) or not self.symbol.strip():
            raise ValueError("symbol cannot be empty.")

        if not isinstance(self.timeframe, str) or not self.timeframe.strip():
            raise ValueError("timeframe cannot be empty.")

        _validate_timezone_aware(self.timestamp, "timestamp")

        normalized_candles = tuple(self.candles)

        if any(not isinstance(candle, OHLCV) for candle in normalized_candles):
            raise TypeError(
                "candles must contain only OHLCV instances."
            )

        object.__setattr__(self, "candles", normalized_candles)

        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping.")

        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )

    @property
    def candle_count(self) -> int:
        """Return the number of candles."""
        return len(self.candles)

    @property
    def latest_candle(self) -> OHLCV | None:
        """Return the latest candle, if available."""
        if not self.candles:
            return None

        return self.candles[-1]

    @property
    def oldest_candle(self) -> OHLCV | None:
        """Return the oldest candle, if available."""
        if not self.candles:
            return None

        return self.candles[0]

    @property
    def latest_timestamp(self) -> datetime | None:
        """Return the timestamp of the latest candle."""
        candle = self.latest_candle
        return candle.timestamp if candle else None

    def has_data(self) -> bool:
        """Return True when at least one candle exists."""
        return bool(self.candles)

    def with_metadata(
        self,
        values: Mapping[str, Any],
    ) -> MarketSnapshot:
        """
        Return a new snapshot with merged metadata.
        """
        merged = dict(self.metadata)
        merged.update(values)

        return MarketSnapshot(
            symbol=self.symbol,
            timeframe=self.timeframe,
            candles=self.candles,
            timestamp=self.timestamp,
            metadata=merged,
        )


@dataclass(frozen=True, slots=True)
class AnalysisContext:
    """
    Context passed into analysis engines.

    This object deliberately contains market data plus metadata,
    without embedding strategy-specific logic.

    Future engines such as:
        - indicators
        - price action
        - supply/demand
        - Elliott Wave
        - harmonic patterns
        - market structure
        - AI analysis

    can consume the same context.
    """

    symbol: str
    timeframe: str
    snapshot: MarketSnapshot
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.symbol, str) or not self.symbol.strip():
            raise ValueError("symbol cannot be empty.")

        if not isinstance(self.timeframe, str) or not self.timeframe.strip():
            raise ValueError("timeframe cannot be empty.")

        if not isinstance(self.snapshot, MarketSnapshot):
            raise TypeError("snapshot must be a MarketSnapshot.")

        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping.")

        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )

    @property
    def candles(self) -> tuple[OHLCV, ...]:
        """Convenience access to snapshot candles."""
        return self.snapshot.candles

    @property
    def latest_candle(self) -> OHLCV | None:
        """Convenience access to the latest candle."""
        return self.snapshot.latest_candle

    def with_metadata(
        self,
        values: Mapping[str, Any],
    ) -> AnalysisContext:
        """
        Return a new analysis context with merged metadata.
        """
        merged = dict(self.metadata)
        merged.update(values)

        return AnalysisContext(
            symbol=self.symbol,
            timeframe=self.timeframe,
            snapshot=self.snapshot,
            metadata=merged,
        )


def build_snapshot(
    symbol: str,
    timeframe: str,
    candles: Iterable[OHLCV],
    timestamp: datetime,
    metadata: Mapping[str, Any] | None = None,
) -> MarketSnapshot:
    """
    Convenience factory for constructing a MarketSnapshot.
    """
    return MarketSnapshot(
        symbol=symbol,
        timeframe=timeframe,
        candles=tuple(candles),
        timestamp=timestamp,
        metadata={} if metadata is None else metadata,
    )


__all__ = [
    "OHLCV",
    "MarketSnapshot",
    "AnalysisContext",
    "build_snapshot",
]
