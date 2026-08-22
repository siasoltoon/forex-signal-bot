
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math
from typing import Any


@dataclass(frozen=True, slots=True)
class Candle:
    """
    Standardized market candle.

    This is the canonical market-data model used throughout
    the data, analysis, signal and risk-management layers.

    The public field names are intentionally kept compatible
    with the existing project.
    """

    symbol: str
    timestamp: datetime

    open: float
    high: float
    low: float
    close: float

    volume: float

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def __post_init__(self) -> None:
        # --------------------------------------------------------------
        # Symbol
        # --------------------------------------------------------------

        if not isinstance(self.symbol, str):
            raise TypeError(
                "symbol must be a string."
            )

        if not self.symbol.strip():
            raise ValueError(
                "symbol cannot be empty."
            )

        # --------------------------------------------------------------
        # Timestamp
        # --------------------------------------------------------------

        if not isinstance(
            self.timestamp,
            datetime,
        ):
            raise TypeError(
                "timestamp must be a datetime."
            )

        if self.timestamp.tzinfo is None:
            raise ValueError(
                "timestamp must be timezone-aware."
            )

        # --------------------------------------------------------------
        # Numeric fields
        # --------------------------------------------------------------

        numeric_values = {
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }

        for field_name, value in numeric_values.items():
            if isinstance(value, bool):
                raise TypeError(
                    f"{field_name} must be a real number."
                )

            try:
                numeric_value = float(value)
            except (TypeError, ValueError) as exc:
                raise TypeError(
                    f"{field_name} must be a real number."
                ) from exc

            if not math.isfinite(numeric_value):
                raise ValueError(
                    f"{field_name} must be finite."
                )

        # --------------------------------------------------------------
        # Price validation
        # --------------------------------------------------------------

        if self.open <= 0:
            raise ValueError(
                "open must be greater than zero."
            )

        if self.high <= 0:
            raise ValueError(
                "high must be greater than zero."
            )

        if self.low <= 0:
            raise ValueError(
                "low must be greater than zero."
            )

        if self.close <= 0:
            raise ValueError(
                "close must be greater than zero."
            )

        if self.volume < 0:
            raise ValueError(
                "volume cannot be negative."
            )

        # --------------------------------------------------------------
        # OHLC structural validation
        # --------------------------------------------------------------

        if self.high < self.low:
            raise ValueError(
                "high cannot be lower than low."
            )

        if self.high < max(
            self.open,
            self.close,
        ):
            raise ValueError(
                "high must be >= open and close."
            )

        if self.low > min(
            self.open,
            self.close,
        ):
            raise ValueError(
                "low must be <= open and close."
            )

    # ------------------------------------------------------------------
    # Basic price properties
    # ------------------------------------------------------------------

    @property
    def typical_price(self) -> float:
        """
        Typical price:

            (high + low + close) / 3
        """

        return (
            self.high
            + self.low
            + self.close
        ) / 3.0

    @property
    def midpoint(self) -> float:
        """
        Midpoint of the candle's high/low range.
        """

        return (
            self.high + self.low
        ) / 2.0

    @property
    def spread(self) -> float:
        """
        Full high-low range.
        """

        return self.high - self.low

    @property
    def range(self) -> float:
        """
        Alias for spread.

        Kept because analytical code commonly refers to
        the candle's total range as `range`.
        """

        return self.spread

    @property
    def range_percent(self) -> float:
        """
        Candle range as a percentage of the low price.

        Returns 0.0 only when the low price is zero, which is
        already prevented by validation.
        """

        return (
            self.spread / self.low
        ) * 100.0

    # ------------------------------------------------------------------
    # Candle body
    # ------------------------------------------------------------------

    @property
    def body(self) -> float:
        """
        Absolute candle body size.
        """

        return abs(
            self.close - self.open
        )

    @property
    def body_signed(self) -> float:
        """
        Signed candle body.

        Positive:
            bullish candle

        Negative:
            bearish candle
        """

        return self.close - self.open

    @property
    def body_percent(self) -> float:
        """
        Candle body size relative to the opening price.
        """

        return (
            self.body / self.open
        ) * 100.0

    @property
    def body_to_range_ratio(self) -> float:
        """
        Ratio of candle body to total candle range.

        Result is between 0 and 1 for valid candles.
        """

        if self.spread == 0:
            return 0.0

        return self.body / self.spread

    # ------------------------------------------------------------------
    # Direction
    # ------------------------------------------------------------------

    @property
    def is_bullish(self) -> bool:
        """
        True when close is above open.
        """

        return self.close > self.open

    @property
    def is_bearish(self) -> bool:
        """
        True when close is below open.
        """

        return self.close < self.open

    @property
    def is_doji(self) -> bool:
        """
        True when open and close are equal.
        """

        return self.close == self.open

    @property
    def direction(self) -> str:
        """
        Human-readable candle direction.

        Returns:
            bullish
            bearish
            neutral
        """

        if self.is_bullish:
            return "bullish"

        if self.is_bearish:
            return "bearish"

        return "neutral"

    # ------------------------------------------------------------------
    # Wicks
    # ------------------------------------------------------------------

    @property
    def upper_wick(self) -> float:
        """
        Upper wick size.
        """

        return (
            self.high
            - max(
                self.open,
                self.close,
            )
        )

    @property
    def lower_wick(self) -> float:
        """
        Lower wick size.
        """

        return (
            min(
                self.open,
                self.close,
            )
            - self.low
        )

    @property
    def upper_wick_percent(self) -> float:
        """
        Upper wick as a percentage of total candle range.
        """

        if self.spread == 0:
            return 0.0

        return (
            self.upper_wick
            / self.spread
        ) * 100.0

    @property
    def lower_wick_percent(self) -> float:
        """
        Lower wick as a percentage of total candle range.
        """

        if self.spread == 0:
            return 0.0

        return (
            self.lower_wick
            / self.spread
        ) * 100.0

    @property
    def wick_to_body_ratio(self) -> float:
        """
        Combined wick size relative to candle body.

        Returns 0.0 for a zero-body candle.
        """

        if self.body == 0:
            return 0.0

        return (
            self.upper_wick
            + self.lower_wick
        ) / self.body

    # ------------------------------------------------------------------
    # Price-change helpers
    # ------------------------------------------------------------------

    def change_from_open(self) -> float:
        """
        Absolute change from open to close.
        """

        return self.close - self.open

    def change_percent(self) -> float:
        """
        Percentage change from open to close.
        """

        return (
            (self.close - self.open)
            / self.open
        ) * 100.0

    # ------------------------------------------------------------------
    # Relative candle strength helpers
    # ------------------------------------------------------------------

    @property
    def close_position(self) -> float:
        """
        Position of close inside the candle range.

        Approximate interpretation:

            0.0 -> close at low
            0.5 -> close near midpoint
            1.0 -> close at high
        """

        if self.spread == 0:
            return 0.5

        return (
            self.close - self.low
        ) / self.spread

    @property
    def open_position(self) -> float:
        """
        Position of open inside the candle range.

        Approximate interpretation:

            0.0 -> open at low
            0.5 -> open near midpoint
            1.0 -> open at high
        """

        if self.spread == 0:
            return 0.5

        return (
            self.open - self.low
        ) / self.spread

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the candle into a JSON-friendly dictionary.

        Timestamp is serialized as an ISO-8601 string.
        """

        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }

    # ------------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------------

    def with_symbol(
        self,
        symbol: str,
    ) -> "Candle":
        """
        Return a copy of this candle with another symbol.

        Useful when a provider uses an internal symbol format
        that needs to be converted to the project's canonical
        representation.
        """

        return Candle(
            symbol=symbol,
            timestamp=self.timestamp,
            open=self.open,
            high=self.high,
            low=self.low,
            close=self.close,
            volume=self.volume,
        )

    def __repr__(self) -> str:
        """
        Compact representation useful in logs and debugging.
        """

        return (
            "Candle("
            f"symbol={self.symbol!r}, "
            f"timestamp={self.timestamp.isoformat()!r}, "
            f"open={self.open!r}, "
            f"high={self.high!r}, "
            f"low={self.low!r}, "
            f"close={self.close!r}, "
            f"volume={self.volume!r}"
            ")"
        )


__all__ = [
    "Candle",
]

