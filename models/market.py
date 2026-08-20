from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class OHLCV:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class MarketSnapshot:
    symbol: str
    timeframe: str
    candles: list[OHLCV]
    timestamp: datetime
    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class AnalysisContext:
    symbol: str
    timeframe: str
    snapshot: MarketSnapshot
    metadata: dict[str, Any] = field(
        default_factory=dict
    )
