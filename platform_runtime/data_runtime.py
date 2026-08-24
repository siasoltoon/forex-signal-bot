from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
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
            if candle.high < candle.low or candle.low <= 0 or candle.close <= 0:
                issues.append("invalid_price")
            if previous and candle.timestamp <= previous:
                issues.append("non_monotonic_timestamp")
            previous = candle.timestamp
        if len({c.timestamp for c in rows}) != len(rows):
            issues.append("duplicate_candle")
        for first, second in zip(rows, rows[1:]):
            if (second.timestamp - first.timestamp).total_seconds() <= 0:
                issues.append("timestamp_gap_or_ordering")
        unique_issues = tuple(dict.fromkeys(issues))
        score = max(0.0, 100.0 - min(100.0, len(unique_issues) * 15.0))
        return DataQuality(score, not unique_issues, unique_issues)


class InMemoryCache:
    def __init__(self, ttl_seconds: int = 30) -> None:
        self.ttl = timedelta(seconds=ttl_seconds)
        self._items: dict[MarketRequest, MarketSnapshot] = {}

    def get(self, request: MarketRequest) -> MarketSnapshot | None:
        snapshot = self._items.get(request)
        if snapshot and datetime.now(timezone.utc) - snapshot.captured_at <= self.ttl:
            return snapshot
        return None

    def put(self, snapshot: MarketSnapshot) -> None:
        self._items[snapshot.request] = snapshot


class AsyncRateLimiter:
    def __init__(self, min_interval_seconds: float = 0.25) -> None:
        self.min_interval = min_interval_seconds
        self._last = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            wait = self.min_interval - (time.monotonic() - self._last)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last = time.monotonic()


class ProviderManager:
    def __init__(self, providers: Sequence[Provider], validator: DataValidator | None = None, cache: InMemoryCache | None = None, retries: int = 2, backoff_seconds: float = 0.5, rate_limiter: AsyncRateLimiter | None = None) -> None:
        self.providers = tuple(providers)
        self.validator = validator or DataValidator()
        self.cache = cache or InMemoryCache()
        self.retries = max(0, retries)
        self.backoff_seconds = max(0.0, backoff_seconds)
        self.rate_limiter = rate_limiter or AsyncRateLimiter()

    async def _fetch_with_retry(self, provider: Provider, request: MarketRequest) -> tuple[Candle, ...]:
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                await self.rate_limiter.acquire()
                return tuple(await provider.fetch(request))
            except Exception as exc:
                last_error = exc
                if attempt < self.retries:
                    await asyncio.sleep(self.backoff_seconds * (2 ** attempt))
        assert last_error is not None
        raise last_error

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
                candles = await self._fetch_with_retry(provider, request)
                quality = self.validator.validate(candles)
                if quality.valid:
                    snapshot = MarketSnapshot(request, candles, provider.name, quality)
                    self.cache.put(snapshot)
                    return snapshot
                failures.extend(f"{provider.name}:{issue}" for issue in quality.issues)
            except Exception as exc:
                failures.append(f"{provider.name}:{type(exc).__name__}")
        raise RuntimeError("NO TRADE: valid market data unavailable; " + ",".join(failures))
