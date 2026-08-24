from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
from market.provider_contracts import Candle, MarketDataProvider
from market.data_quality import DataQuality, MarketDataValidator

@dataclass(frozen=True, slots=True)
class RoutedData:
    provider: str
    candles: tuple[Candle, ...]
    quality: DataQuality

class ProviderRouter:
    def __init__(self, providers: Sequence[MarketDataProvider], validator: MarketDataValidator | None = None) -> None:
        self.providers = tuple(providers)
        self.validator = validator or MarketDataValidator()

    def fetch(self, symbol: str, timeframe: str, limit: int, expected_interval: int | None = None) -> RoutedData:
        errors: list[str] = []
        for provider in self.providers:
            try:
                health = provider.health()
                if not health.healthy:
                    continue
                candles = tuple(provider.fetch_candles(symbol, timeframe, limit))
                quality = self.validator.validate(candles, expected_interval)
                if quality.valid:
                    return RoutedData(provider.name, candles, quality)
                errors.append(provider.name)
            except Exception as exc:
                errors.append(f"{provider.name}:{type(exc).__name__}")
        raise RuntimeError("no valid market-data provider available: " + ",".join(errors))
