from __future__ import annotations

from collections.abc import Sequence

from core.errors import ApplicationError
from core.logger import setup_logger

from data.base import MarketDataProvider
from data.models import Candle


logger = setup_logger()


class DataManager:
    """Central orchestration layer for market-data providers.

    DataManager is deliberately provider-agnostic. Concrete API behavior
    belongs to the provider implementations; this class is responsible for
    selecting providers, validating requests, normalizing returned candles,
    and providing a deterministic fallback path.
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

    # ------------------------------------------------------------------
    # Provider registry
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Primary data access
    # ------------------------------------------------------------------

    async def get_candles(
        self,
        provider_name: str | None,
        symbol: str,
        timeframe: str,
        limit: int = DEFAULT_LIMIT,
    ) -> list[Candle]:
        symbol, timeframe, limit = self._validate_request(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

        provider = (
            self.get_default_provider()
            if provider_name is None
            else self.get_provider(provider_name)
        )

        return await self._fetch_from_provider(
            provider,
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            allow_empty=True,
        )

    async def get_candles_with_fallback(
        self,
        symbol: str,
        timeframe: str,
        limit: int = DEFAULT_LIMIT,
        providers: Sequence[str] | None = None,
    ) -> list[Candle]:
        """Fetch candles using an ordered provider fallback chain.

        An empty result is treated as an unsuccessful market-data attempt,
        because an empty response cannot satisfy a normal candle request.
        Explicit provider order is preserved; otherwise registration order is
        used, with the configured default provider moved to the front.
        """

        symbol, timeframe, limit = self._validate_request(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

        provider_names = self._resolve_fallback_names(providers)
        if not provider_names:
            raise ApplicationError("No market data providers are available.")

        errors: dict[str, str] = {}

        for provider_name in provider_names:
            provider = self.providers.get(provider_name)
            if provider is None:
                errors[provider_name] = "Provider is not registered."
                logger.warning("Fallback provider is not registered: %s", provider_name)
                continue

            try:
                candles = await self._fetch_from_provider(
                    provider,
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=limit,
                    allow_empty=False,
                )
                return candles
            except Exception as error:
                errors[provider_name] = str(error)
                logger.warning(
                    "Provider failed during fallback: %s: %s",
                    provider_name,
                    error,
                )

        raise ApplicationError(
            "All market data providers failed.",
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "limit": limit,
                "provider_errors": errors,
            },
        )

    async def _fetch_from_provider(
        self,
        provider: MarketDataProvider,
        *,
        symbol: str,
        timeframe: str,
        limit: int,
        allow_empty: bool,
    ) -> list[Candle]:
        if not provider.is_configured():
            raise ApplicationError(
                f"Market data provider is not configured: {provider.name}"
            )

        try:
            candles = await provider.get_candles(
                symbol=symbol,
                timeframe=timeframe,
                limit=limit,
            )
        except ApplicationError:
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

        try:
            normalized = self._normalize_candles(
                candles,
                symbol=symbol,
                limit=limit,
            )
        except (TypeError, ValueError) as error:
            raise ApplicationError(
                "Provider returned invalid candle data.",
                {
                    "provider": provider.name,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "limit": limit,
                },
            ) from error

        if not normalized and not allow_empty:
            raise ApplicationError(
                "Provider returned no candles.",
                {
                    "provider": provider.name,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "limit": limit,
                },
            )

        logger.info(
            "Fetched %d candles for %s from %s.",
            len(normalized),
            symbol,
            provider.name,
        )
        return normalized

    # ------------------------------------------------------------------
    # Request and result normalization
    # ------------------------------------------------------------------

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

    def _resolve_fallback_names(
        self,
        providers: Sequence[str] | None,
    ) -> list[str]:
        if providers is not None:
            result: list[str] = []
            seen: set[str] = set()
            for name in providers:
                normalized = self._normalize_provider_name(name)
                if normalized not in seen:
                    seen.add(normalized)
                    result.append(normalized)
            return result

        names = list(self.providers)
        if self.default_provider in names:
            names.remove(self.default_provider)  # type: ignore[arg-type]
            names.insert(0, self.default_provider)  # type: ignore[arg-type]
        return names


__all__ = ["DataManager"]
