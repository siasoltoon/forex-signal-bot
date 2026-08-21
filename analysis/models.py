from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(
    frozen=True
)
class AnalysisCandle:
    """
    Standard OHLCV candle model.
    """

    timestamp: datetime

    open: float

    high: float

    low: float

    close: float

    volume: float = 0.0


    def __post_init__(self) -> None:

        if self.high < self.low:
            raise ValueError(
                "high cannot be lower than low."
            )

        if self.open <= 0:
            raise ValueError(
                "open must be positive."
            )

        if self.high <= 0:
            raise ValueError(
                "high must be positive."
            )

        if self.low <= 0:
            raise ValueError(
                "low must be positive."
            )

        if self.close <= 0:
            raise ValueError(
                "close must be positive."
            )

        if self.volume < 0:
            raise ValueError(
                "volume cannot be negative."
            )


    @property
    def body_size(self) -> float:

        return abs(
            self.close - self.open
        )


    @property
    def is_bullish(self) -> bool:

        return self.close > self.open


    @property
    def is_bearish(self) -> bool:

        return self.close < self.open



@dataclass(
    frozen=True
)
class SignalComponent:
    """
    Single analysis signal component.

    Used by scoring engine to combine
    different analysis modules.
    """

    name: str

    direction: str

    weight: float

    confidence: float


    def __post_init__(self) -> None:

        if not self.name:
            raise ValueError(
                "name cannot be empty."
            )

        if self.direction not in (
            "bullish",
            "bearish",
            "neutral",
        ):
            raise ValueError(
                "invalid direction."
            )

        if self.weight < 0:
            raise ValueError(
                "weight cannot be negative."
            )

        if not 0 <= self.confidence <= 1:
            raise ValueError(
                "confidence must be between 0 and 1."
            )



@dataclass(
    frozen=True
)
class AnalysisScore:
    """
    Combined analysis score.
    """

    bullish: float = 0.0

    bearish: float = 0.0

    confidence: float = 0.0


    def __post_init__(self) -> None:

        if self.bullish < 0:
            raise ValueError(
                "bullish cannot be negative."
            )

        if self.bearish < 0:
            raise ValueError(
                "bearish cannot be negative."
            )

        if not 0 <= self.confidence <= 1:
            raise ValueError(
                "confidence must be between 0 and 1."
            )


    @property
    def bias(self) -> str:

        if self.bullish > self.bearish:
            return "bullish"

        if self.bearish > self.bullish:
            return "bearish"

        return "neutral"



@dataclass(
    frozen=True
)
class PriceData:
    """
    Generic price data.
    """

    close: float

    timestamp: datetime | None = None
