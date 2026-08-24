from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Sequence

@dataclass(frozen=True, slots=True)
class Candle:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None

@dataclass(frozen=True, slots=True)
class ProviderHealth:
    provider: str
    healthy: bool
    latency_ms: float = 0.0
    message: str = ""

class MarketProvider(Protocol):
    name: str
    def fetch(self, symbol: str, timeframe: str, limit: int) -> Sequence[Candle]: ...
    def health(self) -> ProviderHealth: ...

@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    symbol: str
    timeframe: str
    candles: tuple[Candle, ...]
    provider: str
    quality_score: float
    as_of: int
