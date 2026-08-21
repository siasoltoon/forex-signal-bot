from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math


@dataclass(frozen=True, slots=True)
class Candle:
    """
    Standardized market candle.

    This model is provider-independent and is used
    throughout the data and analysis layers.
    """

    symbol: str
    timestamp: datetime

    open: float
    high: float
    low: float
    close: float

    volume: float

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError(
                "symbol cannot be empty."
            )

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

        prices = (
            self.open,
            self.high,
            self.low,
            self.close,
            self.volume,
        )

        if not all(
            math.isfinite(
                float(value)
            )
            for value in prices
        ):
            raise ValueError(
                "Candle values must be finite."
            )

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

    @property
    def typical_price(self) -> float:
        """
        Calculate the typical price.

        Formula:
            (high + low + close) / 3
        """

        return (
            self.high
            + self.low
            + self.close
        ) / 3.0

    @property
    def spread(self) -> float:
        """
        High-low price range.
        """

        return self.high - self.low

    @property
    def body(self) -> float:
        """
        Absolute candle body size.
        """

        return abs(
            self.close - self.open
        )

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
