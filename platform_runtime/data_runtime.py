from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Iterable, Protocol, Sequence


class Market(str, Enum):
    FOREX = "forex"
    CRYPTO = "crypto"
    STOCKS = "stocks"
    INDICES = "indices"
    COMMODITIES = "commodities"


@dataclass(frozen=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None


@dataclass(frozen=True)
class MarketRequest:
    market: Market
    symbol: str
    timeframe: str
    limit: int = 500


@dataclass(frozen=True)
class DataQuality:
    score: float
    valid: bool
    issues: tuple[str, ...] = ()


@dataclass(frozen=True)
class MarketSnapshot:
    request: MarketRequest
    candles: tuple[Candle, ...]
    source: str
    quality: DataQuality
    captured_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class Provider(Protocol):
    name: str
    async def fetch(self, request: MarketRequest) -> Sequence[Candle]: ...
    async def health(self) -> bool: ...


class DataValidator:
    def validate(self, candles: Iterable[Candle]) -> DataQuality:
        rows = list(candles)
        issues: list[str] = []
        if not rows:
            return DataQuality(0.0, False, ("empty_dataset",))
        previous = None
        for candle in rows:
            if candle.high < max(candle.open, candle.close) or candle.low > min(candle.open, candle.close):
                issues.append("invalid_ohlc")
            if candle.high < candle.low:
                issues.append("invalid_range")
            if previous and candle.timestamp <= previous:
                issues.append("non_monotonic_timestamp")
            previous = candle.timestamp
        unique = len({c.timestamp for c in rows})
        if unique != len(rows):
            issues.append("duplicate_candle")
        score = max(0.0, 100.0 - min(100.0, len(set(issues)) * 15.0))
        return DataQuality(score, not issues, tuple(dict.fromkeys(issues)))


class InMemoryCache:
    def __init__(self) -> None:
        self._items: dict[MarketRequest, MarketSnapshot] = {}

    def get(self, request: MarketRequest) -> MarketSnapshot | None:
        return self._items.get(request)

    def put(self, snapshot: MarketSnapshot) -> None:
        self._items[snapshot.request] = snapshot


class ProviderManager:
    def __init__(self, providers: Sequence[Provider], validator: DataValidator | None = None, cache: InMemoryCache | None = None) -> None:
        self.providers = tuple(providers)
        self.validator = validator or DataValidator()
        self.cache = cache or InMemoryCache()

    async def snapshot(self, request: MarketRequest) -> MarketSnapshot:
        cached = self.cache.get(request)
        if cached and cached.quality.valid:
            return cached
        failures: list[str] = []
        for provider in self.providers:
            try:
                if not await provider.health():
                    failures.append(f"{provider.name}:unhealthy")
                    continue
                candles = tuple(await provider.fetch(request))
                quality = self.validator.validate(candles)
                if quality.valid:
                    snapshot = MarketSnapshot(request, candles, provider.name, quality)
                    self.cache.put(snapshot)
                    return snapshot
                failures.extend(f"{provider.name}:{issue}" for issue in quality.issues)
            except Exception as exc:  # provider isolation; next provider is attempted
                failures.append(f"{provider.name}:{type(exc).__name__}")
        raise RuntimeError("NO TRADE: valid market data unavailable; " + ",".join(failures))
