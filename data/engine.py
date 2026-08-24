from __future__ import annotations

from data.cache import DataCache
from data.contracts import MarketDataRequest, MarketDataResult
from data.failover import ProviderRouter
from data.validator import validate_candles


class DataEngine:
    def __init__(self, router: ProviderRouter, cache: DataCache | None = None) -> None:
        self.router = router
        self.cache = cache

    def get(self, request: MarketDataRequest, *, expected_seconds: int | None = None, stale_after_seconds: int | None = None) -> MarketDataResult:
        if self.cache:
            cached = self.cache.get(request)
            if cached is not None and cached.quality.valid:
                return cached
        result = self.router.fetch(request)
        quality = validate_candles(result.candles, expected_seconds=expected_seconds, stale_after_seconds=stale_after_seconds)
        validated = MarketDataResult(request, result.candles, result.provider, quality)
        if not quality.valid:
            raise ValueError(f"invalid market data: {quality.reason}")
        if self.cache:
            self.cache.put(request, validated)
        return validated
