from __future__ import annotations

from dataclasses import dataclass


@dataclass(
    frozen=True
)
class Candle:
    """
    Standard OHLC candle model.

    Used by:
    - Candlestick analysis
    - Price action
    - Supply/Demand
    - Future trading engines
    """

    open: float

    high: float

    low: float

    close: float

    volume: float = 0.0
