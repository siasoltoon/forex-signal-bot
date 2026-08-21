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
    def body_size(
        self,
    ) -> float:

        return abs(
            self.close - self.open
        )


    @property
    def is_bullish(
        self,
    ) -> bool:

        return self.close > self.open


    @property
    def is_bearish(
        self,
    ) -> bool:

        return self.close < self.open



@dataclass(
    frozen=True
)
class SignalComponent:
    """
    Single scoring component.

    Used by analysis scoring engine.
    """

    name: str

    score: float

    reason: str


    def __post_init__(
        self,
    ) -> None:

        if not self.name:
            raise ValueError(
                "name cannot be empty."
            )

        if not isinstance(
            self.score,
            (int, float),
        ):
            raise TypeError(
                "score must be numeric."
            )

        if not self.reason:
            raise ValueError(
                "reason cannot be empty."
            )



@dataclass(
    frozen=True
)
class AnalysisScore:
    """
    Final analysis score.
    """

    score: float

    confidence: float

    signal: str


    def __post_init__(
        self,
    ) -> None:

        if not isinstance(
            self.score,
            (int, float),
        ):
            raise TypeError(
                "score must be numeric."
            )

        if not 0 <= self.confidence <= 1:
            raise ValueError(
                "confidence must be between 0 and 1."
            )

        if self.signal not in (
            "buy",
            "sell",
            "hold",
        ):
            raise ValueError(
                "invalid signal."
            )



@dataclass(
    frozen=True
)
class PriceData:
    """
    Generic price container.
    """

    close: float

    timestamp: datetime | None = None
