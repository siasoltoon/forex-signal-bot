from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(
    frozen=True
)
class AnalysisCandle:
    """
    Standard OHLCV candle model
    used by analysis engines.
    """

    timestamp: datetime

    open: float

    high: float

    low: float

    close: float

    volume: float = 0.0


    def __post_init__(self) -> None:
        """
        Validate candle values.
        """

        if self.high < self.low:
            raise ValueError(
                "high cannot be lower than low."
            )

        if self.open <= 0:
            raise ValueError(
                "open price must be positive."
            )

        if self.high <= 0:
            raise ValueError(
                "high price must be positive."
            )

        if self.low <= 0:
            raise ValueError(
                "low price must be positive."
            )

        if self.close <= 0:
            raise ValueError(
                "close price must be positive."
            )

        if self.volume < 0:
            raise ValueError(
                "volume cannot be negative."
            )


    @property
    def body_size(self) -> float:
        """
        Candle body size.
        """

        return abs(
            self.close - self.open
        )


    @property
    def is_bullish(self) -> bool:
        """
        Bullish candle check.
        """

        return self.close > self.open


    @property
    def is_bearish(self) -> bool:
        """
        Bearish candle check.
        """

        return self.close < self.open
