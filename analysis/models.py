from __future__ import annotations

from dataclasses import dataclass


@dataclass(
    frozen=True
)
class AnalysisScore:
    """
    Standard analysis scoring result.

    score:
        Range: -100 to +100

    direction:
        BUY / SELL / NEUTRAL

    confidence:
        Range: 0.0 to 1.0
    """

    score: float

    direction: str

    confidence: float


@dataclass(
    frozen=True
)
class SignalComponent:
    """
    Single analysis component contribution.

    Example:
    RSI contribution
    MACD contribution
    Trend contribution
    """

    name: str

    score: float

    reason: str
