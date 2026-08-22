from __future__ import annotations

from collections.abc import Sequence

from core.errors import ApplicationError
from core.logger import setup_logger

from data.base import MarketDataProvider
from data.models import Candle
from data.provider_manager import ProviderManager

logger = setup_logger()


class DataManager:
    """Public facade for market-data access.

    DataManager owns provider registration and explicit-provider access.
    Provider health, retry, cooldown, fallback, and provider-level result
    handling are delegated to ProviderManager so those policies have one
    implementation in the data layer.
    """

    DEFAULT_LIMIT = MarketDataProvider.DEFAULT_LIMIT
    MAX_LIMIT = MarketDataProvider.MAX_LIMIT

    def __init__(self, default_provider: str | None = None) -> None:
        self.providers: dict[str, MarketDataProvider] = {}
        self.default_provider = (
            self._normalize_provider_name(default_provider)
            if default_provider is not None
            else None
        )
        self._provider_manager: ProviderManager | None = None

    def register(self, provider: MarketDataProvider) -> None:
        if not isinstance(provider, MarketDataProvider):
            raise TypeError("provider must implement MarketDataProvider.")

        name = getattr(provider, "name", None)
        if not isinstance(name, str):
            raise TypeError("provider.name must be a string.")

        name = self._normalize_provider_name(name)
        if name in self.providers:
            raise ApplicationError(f"Provider already registered: {name}")

        self.providers[name] = provider
        if self.default_provider is None:
            self.default_provider = name
        self._sync_provider_manager()
        logger.info("Market data provider registered: %s", name)

    def unregister(self, name: str) -> None:
        normalized_name = self._normalize_provider_name(name)
        if normalized_name not in self.providers:
            raise ApplicationError(
                f"Market data provider not found: {normalized_name}"
            )

        del self.providers[normalized_name]
        if self.default_provider == normalized_name:
            self.default_provider = next(iter(self.providers), None)
        self._sync_provider_manager()
        logger.info("Market data provider removed: %s", normalized_name)

    def has_provider(self, name: str) -> bool:
        return self._normalize_provider_name(name) in self.providers

    def get_provider(self, name: str) -> MarketDataProvider:
        normalized_name = self._normalize_provider_name(name)
        provider = self.providers.get(normalized_name)
        if provider is None:
            raise ApplicationError(
                f"Market data provider not found: {normalized_name}"
            )
        return provider

    def set_default_provider(self, name: str) -> None:
        normalized_name = self._normalize_provider_name(name)
        if normalized_name not in self.providers:
            raise ApplicationError(
                f"Cannot set unknown provider as default: {normalized_name}"
            )
        self.default_provider = normalized_name
        logger.info("Default market data provider set to: %s", normalized_name)

    def get_default_provider(self) -> MarketDataProvider:
        if not self.default_provider:
            raise ApplicationError(
                "No default market data provider has been configured."
            )
        return self.get_provider(self.default_provider)

    def list_providers(self) -> list[str]:
        return list(self.providers)

    def provider_count(self) -> int:
        return len(self.providers)

    async def get_candles(
        self,
        provider_name: str | None,
        symbol: str,
        timeframe: str,
        limit: int = DEFAULT_LIMIT,
    ) -> list[Candle]:
        symbol, timeframe, limit = self._validate_request(symbol, timeframe, limit)
        provider = (
            self.get_default_provider()
            if provider_name is None
            else self.get_provider(provider_name)
        )
        return await self._fetch_explicit_via_manager(
            provider,
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

    async def get_candles_with_fallback(
        self,
        symbol: str,
        timeframe: str,
        limit: int = DEFAULT_LIMIT,
        providers: Sequence[str] | None = None,
    ) -> list[Candle]:
        """Fetch candles through ProviderManager's fallback policy."""
        symbol, timeframe, limit = self._validate_request(symbol, timeframe, limit)

        if not self.providers:
            raise ApplicationError("No market data providers are available.")

        manager = self._provider_manager
        if providers is not None:
            requested: list[MarketDataProvider] = []
            for name in providers:
                normalized = self._normalize_provider_name(name)
                provider = self.providers.get(normalized)
                if provider is None:
                    raise ApplicationError(
                        f"Market data provider not found: {normalized}"
                    )
                requested.append(provider)
            if not requested:
                raise ApplicationError("No market data providers are available.")
            manager = ProviderManager(providers=requested)

        if manager is None:
            raise ApplicationError("No market data providers are available.")

        return await manager.get_candles(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

    def _sync_provider_manager(self) -> None:
        if not self.providers:
            self._provider_manager = None
            return

        provider_objects = list(self.providers.values())
        if self._provider_manager is None:
            self._provider_manager = ProviderManager(providers=provider_objects)
        else:
            self._provider_manager.set_providers(provider_objects)

    async def _fetch_explicit_via_manager(
        self,
        provider: MarketDataProvider,
        *,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> list[Candle]:
        """Fetch one explicitly selected provider through ProviderManager.

        The explicit DataManager contract intentionally differs from the
        fallback contract: an empty result is valid and provider-level
        ApplicationError instances are preserved. ProviderManager remains
        responsible for invoking and validating the provider result.
        """
        if not provider.is_configured():
            raise ApplicationError(
                f"Market data provider is not configured: {provider.name}"
            )

        manager = ProviderManager(
            providers=[provider],
            retries=0,
            retry_delay=0,
            cooldown_seconds=0,
        )

        try:
            return await manager.get_candles(
                symbol=symbol,
                timeframe=timeframe,
                limit=limit,
            )
        except ApplicationError as error:
            if (
                error.message == "Provider returned no candles."
                and error.details.get("provider") == provider.name
                and error.details.get("symbol") == symbol
                and error.details.get("timeframe") == timeframe
            ):
                return []
            raise
        except Exception as error:
            logger.exception(
                "Market data request failed. Provider=%s Symbol=%s Timeframe=%s",
                provider.name,
                symbol,
                timeframe,
            )
            raise ApplicationError(
                "Failed to fetch market candles.",
                {
                    "provider": provider.name,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "limit": limit,
                },
            ) from error

    @staticmethod
    def _normalize_provider_name(name: str) -> str:
        if not isinstance(name, str):
            raise TypeError("Provider name must be a string.")
        normalized = name.strip().lower()
        if not normalized:
            raise ApplicationError("Provider name cannot be empty.")
        return normalized

    @classmethod
    def _validate_request(
        cls,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> tuple[str, str, int]:
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string.")
        symbol = MarketDataProvider.normalize_symbol(symbol)

        if not isinstance(timeframe, str):
            raise TypeError("timeframe must be a string.")
        timeframe = MarketDataProvider.normalize_timeframe(timeframe)

        if isinstance(limit, bool) or not isinstance(limit, int):
            raise TypeError("limit must be an integer.")
        if limit < 1:
            raise ValueError("limit must be greater than zero.")
        if limit > cls.MAX_LIMIT:
            raise ValueError(f"limit cannot exceed {cls.MAX_LIMIT}.")

        return symbol, timeframe, limit

    @classmethod
    def _normalize_candles(
        cls,
        candles: list[Candle] | Sequence[Candle],
        *,
        symbol: str,
        limit: int,
    ) -> list[Candle]:
        if not isinstance(candles, list):
            raise TypeError("Provider must return a list of candles.")

        normalized = MarketDataProvider.normalize_candles(
            candles,
            expected_symbol=symbol,
            deduplicate=True,
        )
        return MarketDataProvider.apply_limit(normalized, limit)


__all__ = ["DataManager"]
