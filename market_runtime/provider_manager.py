from __future__ import annotations
from dataclasses import dataclass
from time import monotonic, sleep
from typing import Callable, Sequence
from .contracts import Candle, MarketProvider, ProviderHealth, MarketSnapshot
from .cache import TTLCache

@dataclass(frozen=True, slots=True)
class ProviderAttempt:
    provider: str
    success: bool
    latency_ms: float
    error: str = ""

class RateLimiter:
    def __init__(self, min_interval: float = 0.0) -> None:
        self.min_interval=max(0.0,min_interval); self._last=0.0
    def wait(self) -> None:
        delay=self.min_interval-(monotonic()-self._last)
        if delay>0: sleep(delay)
        self._last=monotonic()

class ProviderManager:
    def __init__(self, providers: Sequence[MarketProvider], cache: TTLCache[tuple[Candle,...]] | None=None, limiter: RateLimiter | None=None) -> None:
        self.providers=tuple(providers); self.cache=cache or TTLCache(); self.limiter=limiter or RateLimiter(); self.history: list[ProviderAttempt]=[]
    def fetch(self, symbol: str, timeframe: str, limit: int, ttl: float=5.0) -> MarketSnapshot:
        key=f"{symbol}:{timeframe}:{limit}"
        cached=self.cache.get(key)
        if cached is not None:
            return MarketSnapshot(symbol,timeframe,cached,"cache",1.0,cached[-1].timestamp if cached else 0)
        errors=[]
        for provider in self.providers:
            start=monotonic(); self.limiter.wait()
            try:
                candles=tuple(provider.fetch(symbol,timeframe,limit)); health=provider.health()
                if not candles: raise ValueError("provider returned no candles")
                self.history.append(ProviderAttempt(provider.name,True,(monotonic()-start)*1000))
                self.cache.put(key,candles,ttl)
                return MarketSnapshot(symbol,timeframe,candles,provider.name,1.0,candles[-1].timestamp)
            except Exception as exc:
                self.history.append(ProviderAttempt(provider.name,False,(monotonic()-start)*1000,str(exc))); errors.append(str(exc))
        raise RuntimeError("all market providers failed: " + " | ".join(errors))
