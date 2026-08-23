from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Sequence

from .data_runtime import Candle, DataQuality, DataValidator, InMemoryCache, MarketRequest, MarketSnapshot, Provider


@dataclass(frozen=True)
class ProviderAttempt:
    provider: str
    success: bool
    error: str | None = None
    latency_ms: float | None = None


class RetryPolicy:
    def __init__(self, attempts: int = 3, base_delay: float = 0.25) -> None:
        self.attempts = max(1, attempts)
        self.base_delay = max(0.0, base_delay)

    async def run(self, operation):
        last: Exception | None = None
        for index in range(self.attempts):
            try:
                return await operation()
            except Exception as exc:
                last = exc
                if index + 1 < self.attempts:
                    await asyncio.sleep(self.base_delay * (2**index))
        raise last or RuntimeError("operation_failed")


class AsyncRateLimiter:
    def __init__(self, rate_per_second: float) -> None:
        self.interval = 0.0 if rate_per_second <= 0 else 1.0 / rate_per_second
        self._lock = asyncio.Lock()
        self._last = 0.0

    async def wait(self) -> None:
        async with self._lock:
            delay = self.interval - (time.monotonic() - self._last)
            if delay > 0:
                await asyncio.sleep(delay)
            self._last = time.monotonic()


class ProviderHealthRegistry:
    def __init__(self) -> None:
        self._states: dict[str, bool] = {}

    def set(self, provider: str, healthy: bool) -> None:
        self._states[provider] = healthy

    def healthy(self, provider: str) -> bool | None:
        return self._states.get(provider)

    def snapshot(self) -> dict[str, bool]:
        return dict(self._states)


class ResilientProviderManager:
    def __init__(self, providers: Sequence[Provider], *, validator: DataValidator | None = None,
                 cache: InMemoryCache | None = None, retry: RetryPolicy | None = None,
                 limiter: AsyncRateLimiter | None = None) -> None:
        self.providers = tuple(providers)
        self.validator = validator or DataValidator()
        self.cache = cache or InMemoryCache()
        self.retry = retry or RetryPolicy()
        self.limiter = limiter or AsyncRateLimiter(0)
        self.health_registry = ProviderHealthRegistry()

    async def snapshot(self, request: MarketRequest) -> MarketSnapshot:
        cached = self.cache.get(request)
        if cached and cached.quality.valid:
            return cached
        attempts: list[ProviderAttempt] = []
        for provider in self.providers:
            started = time.perf_counter()
            try:
                await self.limiter.wait()
                healthy = await self.retry.run(provider.health)
                self.health_registry.set(provider.name, healthy)
                if not healthy:
                    attempts.append(ProviderAttempt(provider.name, False, "unhealthy"))
                    continue
                candles = tuple(await self.retry.run(lambda: provider.fetch(request)))
                quality = self.validator.validate(candles)
                latency = (time.perf_counter() - started) * 1000
                if quality.valid:
                    snapshot = MarketSnapshot(request, candles, provider.name, quality)
                    self.cache.put(snapshot)
                    return snapshot
                attempts.append(ProviderAttempt(provider.name, False, ",".join(quality.issues), latency))
            except Exception as exc:
                self.health_registry.set(provider.name, False)
                attempts.append(ProviderAttempt(provider.name, False, type(exc).__name__, (time.perf_counter() - started) * 1000))
        raise RuntimeError("NO TRADE: all market-data providers failed; " + ";".join(a.provider + ":" + str(a.error) for a in attempts))
