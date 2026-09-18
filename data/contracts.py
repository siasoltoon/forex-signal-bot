from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Market(StrEnum):
    FOREX = "FOREX"
    CRYPTO = "CRYPTO"
    STOCKS = "STOCKS"
    INDICES = "INDICES"
    COMMODITIES = "COMMODITIES"


@dataclass(frozen=True, slots=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None


@dataclass(frozen=True, slots=True)
class MarketDataRequest:
    market: Market
    symbol: str
    timeframe: str
    limit: int = 500


@dataclass(frozen=True, slots=True)
class DataQuality:
    valid: bool
    score: float
    missing: int = 0
    duplicates: int = 0
    stale: bool = False
    outliers: int = 0
    gaps: int = 0
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class MarketDataResult:
    request: MarketDataRequest
    candles: tuple[Candle, ...]
    provider: str
    quality: DataQuality
