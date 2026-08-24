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
    latency_ms: float
    message: str = ""

class MarketDataProvider(Protocol):
    name: str
    def fetch_candles(self, symbol: str, timeframe: str, limit: int) -> Sequence[Candle]: ...
    def health(self) -> ProviderHealth: ...
