
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Iterable

from core.errors import ApplicationError
from core.logger import setup_logger

from data.base import MarketDataProvider
from data.factory import ProviderFactory
from data.models import Candle


logger = setup_logger()


@dataclass(frozen=True, slots=True)
class ProviderFailure:
    """Information about a failed provider attempt."""
    provider: str
    attempt: int
    error_type: str
    message: str


ProviderReference = str | MarketDataProvider


class ProviderManager:
    """High-level manager for market-data providers."""

    DEFAULT_PROVIDERS: tuple[str, ...] = (
        "oanda",
        "finnhub",
        "alphavantage",
    )
    DEFAULT_RETRIES = 2

    def __init__(
        self,
        providers: Iterable[ProviderReference] | None = None,
        *,
        retries: int = DEFAULT_RETRIES,
        retry_delay: float = 0.5,
        cooldown_seconds: float = 30.0,
    ) -> None:
        if providers is None:
            providers = self.DEFAULT_PROVIDERS
        raw_providers = list(providers)
        if not raw_providers:
            raise ValueError("At least one provider must be configured.")
        self.retries = self._validate_non_negative_int(retries, "retries")
        self.retry_delay = self._validate_non_negative_number(retry_delay, "retry_delay")
        self.cooldown_seconds = self._validate_non_negative_number(cooldown_seconds, "cooldown_seconds")
        self._providers: tuple[str, ...]
        self._provider_instances: dict[str, MarketDataProvider] = {}
        self._provider_objects: dict[str, MarketDataProvider] = {}
        provider_names: list[str] = []
        for index, provider_reference in enumerate(raw_providers):
            if isinstance(provider_reference, str):
                provider_name = ProviderFactory.normalize_name(provider_reference)
                if not ProviderFactory.is_supported(provider_name):
                    raise ApplicationError("Unknown market data provider.", {"provider": provider_name, "available": ProviderFactory.available()})
                canonical_name = provider_name
                provider_instance = None
            else:
                provider_instance = provider_reference
                if not self._is_provider_instance(provider_instance):
                    raise TypeError("Each provider must be either a provider name string or an object implementing get_candles(). " f"Invalid provider at index {index}: " f"{type(provider_reference).__name__}")
                canonical_name = self._provider_instance_name(provider_instance, index)
            if canonical_name in provider_names:
                continue
            provider_names.append(canonical_name)
            if provider_instance is not None:
                self._provider_objects[canonical_name] = provider_instance
        self._providers = tuple(provider_names)
        if not self._providers:
            raise ValueError("At least one provider must be configured.")
        self._cooldowns: dict[str, float] = {}
        self._last_failures: list[ProviderFailure] = []

    @staticmethod
    def _validate_non_negative_int(value: int, name: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} must be an integer.")
        if value < 0:
            raise ValueError(f"{name} cannot be negative.")
        return value

    @staticmethod
    def _validate_non_negative_number(value: float, name: str) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be a number.")
        if value < 0:
            raise ValueError(f"{name} cannot be negative.")
        return float(value)

    @staticmethod
    def _is_provider_instance(provider: object) -> bool:
        return callable(getattr(provider, "get_candles", None))

    @staticmethod
    def _provider_instance_name(provider: MarketDataProvider, index: int) -> str:
        name = getattr(provider, "name", None)
        if isinstance(name, str) and name.strip():
            try:
                return ProviderFactory.normalize_name(name)
            except (TypeError, ValueError):
                pass
        provider_name = getattr(provider, "provider_name", None)
        if isinstance(provider_name, str) and provider_name.strip():
            try:
                return ProviderFactory.normalize_name(provider_name)
            except (TypeError, ValueError):
                pass
        normalized = provider.__class__.__name__.strip().lower()
        if normalized.endswith("provider"):
            normalized = normalized[:-len("provider")]
        if not normalized:
            normalized = "provider"
        return f"{normalized}_{index}"

    @property
    def providers(self) -> tuple[str, ...]:
        return self._providers

    def set_providers(self, providers: Iterable[ProviderReference]) -> None:
        raw_providers = list(providers)
        if not raw_providers:
            raise ValueError("At least one provider must be configured.")
        normalized: list[str] = []
        new_objects: dict[str, MarketDataProvider] = {}
        for index, provider_reference in enumerate(raw_providers):
            if isinstance(provider_reference, str):
                provider_name = ProviderFactory.normalize_name(provider_reference)
                if not ProviderFactory.is_supported(provider_name):
                    raise ApplicationError("Unknown market data provider.", {"provider": provider_name, "available": ProviderFactory.available()})
                canonical_name = provider_name
            else:
                if not self._is_provider_instance(provider_reference):
                    raise TypeError("Each provider must be either a provider name string or an object implementing get_candles().")
                canonical_name = self._provider_instance_name(provider_reference, index)
                new_objects[canonical_name] = provider_reference
            if canonical_name not in normalized:
                normalized.append(canonical_name)
        self._providers = tuple(normalized)
        self._provider_objects.update(new_objects)

    def _get_provider(self, provider_name: str) -> MarketDataProvider:
        normalized_name = ProviderFactory.normalize_name(provider_name) if provider_name in self._provider_objects else provider_name
        injected = self._provider_objects.get(normalized_name)
        if injected is not None:
            return injected
        provider = self._provider_instances.get(normalized_name)
        if provider is None:
            provider = ProviderFactory.create(normalized_name)
            self._provider_instances[normalized_name] = provider
        return provider

    def clear_instances(self) -> None:
        self._provider_instances.clear()

    def _is_in_cooldown(self, provider_name: str) -> bool:
        expires_at = self._cooldowns.get(provider_name)
        if expires_at is None:
            return False
        if time.monotonic() >= expires_at:
            self._cooldowns.pop(provider_name, None)
            return False
        return True

    def _put_in_cooldown(self, provider_name: str) -> None:
        if self.cooldown_seconds <= 0:
            return
        self._cooldowns[provider_name] = time.monotonic() + self.cooldown_seconds

    def clear_cooldown(self, provider_name: str) -> None:
        if provider_name in self._cooldowns:
            self._cooldowns.pop(provider_name, None)
            return
        try:
            normalized_name = ProviderFactory.normalize_name(provider_name)
        except (TypeError, ValueError):
            normalized_name = provider_name
        self._cooldowns.pop(normalized_name, None)

    def clear_all_cooldowns(self) -> None:
        self._cooldowns.clear()

    @property
    def last_failures(self) -> tuple[ProviderFailure, ...]:
        return tuple(self._last_failures)

    async def _request_with_retry(self, provider_name: str, provider: MarketDataProvider, *, symbol: str, timeframe: str, limit: int) -> list[Candle]:
        total_attempts = self.retries + 1
        last_error: Exception | None = None
        for attempt in range(1, total_attempts + 1):
            try:
                candles = await provider.get_candles(symbol=symbol, timeframe=timeframe, limit=limit)
                validated = self._validate_result(provider_name=provider_name, candles=candles, symbol=symbol)
                if not validated:
                    raise ApplicationError("Provider returned no candles.", {"provider": provider_name, "symbol": symbol, "timeframe": timeframe})
                return validated
            except Exception as error:
                last_error = error
                self._last_failures.append(ProviderFailure(provider=provider_name, attempt=attempt, error_type=type(error).__name__, message=str(error)))
                logger.warning("Provider %s failed (attempt %d/%d): %s", provider_name, attempt, total_attempts, error)
                if attempt >= total_attempts:
                    break
                if self.retry_delay > 0:
                    await asyncio.sleep(self.retry_delay * (2 ** (attempt - 1)))
        assert last_error is not None
        raise last_error

    @staticmethod
    def _validate_result(provider_name: str, candles: object, symbol: str) -> list[Candle]:
        if not isinstance(candles, list):
            raise ApplicationError("Provider returned an invalid candle collection.", {"provider": provider_name, "symbol": symbol, "expected": "list[Candle]", "actual": type(candles).__name__})
        for index, candle in enumerate(candles):
            if not isinstance(candle, Candle):
                cause = TypeError(f"Invalid candle at index {index}: expected Candle, got {type(candle).__name__}.")
                raise ApplicationError("Provider returned invalid candle data.", {"provider": provider_name, "symbol": symbol, "index": index, "expected": "Candle", "actual": type(candle).__name__}) from cause
        return list(candles)

    @staticmethod
    def _normalize_candles(candles: list[Candle], *, limit: int) -> list[Candle]:
        unique: dict[tuple[str, object], Candle] = {}
        for candle in candles:
            unique[(candle.symbol, candle.timestamp)] = candle
        normalized = sorted(unique.values(), key=lambda candle: candle.timestamp)
        if len(normalized) > limit:
            normalized = normalized[-limit:]
        return normalized

    async def get_candles(self, symbol: str, timeframe: str, limit: int = 100) -> list[Candle]:
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string.")
        if not symbol.strip():
            raise ValueError("symbol cannot be empty.")
        if not isinstance(timeframe, str):
            raise TypeError("timeframe must be a string.")
        if not timeframe.strip():
            raise ValueError("timeframe cannot be empty.")
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise TypeError("limit must be an integer.")
        if limit < 1:
            raise ValueError("limit must be greater than zero.")
        normalized_symbol = symbol.strip().upper()
        normalized_timeframe = timeframe.strip().upper()
        self._last_failures = []
        attempted_providers = 0
        skipped_providers = 0
        for provider_name in self._providers:
            if self._is_in_cooldown(provider_name):
                skipped_providers += 1
                logger.info("Skipping provider %s because it is in cooldown.", provider_name)
                continue
            attempted_providers += 1
            try:
                provider = self._get_provider(provider_name)
                candles = await self._request_with_retry(provider_name, provider, symbol=normalized_symbol, timeframe=normalized_timeframe, limit=limit)
                candles = self._normalize_candles(candles, limit=limit)
                if not candles:
                    raise ApplicationError("Provider returned no usable candles.", {"provider": provider_name, "symbol": normalized_symbol, "timeframe": normalized_timeframe})
                self._cooldowns.pop(provider_name, None)
                logger.info("Provider %s successfully returned %d candles for %s (%s).", provider_name, len(candles), normalized_symbol, normalized_timeframe)
                return candles
            except Exception:
                self._put_in_cooldown(provider_name)
                logger.warning("Provider %s exhausted. Trying next provider.", provider_name)
                continue
        raise ApplicationError("All market data providers failed.", {"symbol": normalized_symbol, "timeframe": normalized_timeframe, "limit": limit, "providers": list(self._providers), "attempted_providers": attempted_providers, "skipped_providers": skipped_providers, "failures": [{"provider": f.provider, "attempt": f.attempt, "error_type": f.error_type, "message": f.message} for f in self._last_failures]})

    def status(self) -> dict[str, object]:
        now = time.monotonic()
        cooldowns: dict[str, float] = {}
        for provider_name, expires_at in self._cooldowns.items():
            cooldowns[provider_name] = max(0.0, expires_at - now)
        return {"providers": list(self._providers), "cached_instances": list(self._provider_instances.keys()), "injected_instances": list(self._provider_objects.keys()), "cooldowns": cooldowns, "retries": self.retries, "retry_delay": self.retry_delay, "cooldown_seconds": self.cooldown_seconds}


__all__ = ["ProviderFailure", "ProviderManager"]
