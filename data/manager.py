from __future__ import annotations

from collections.abc import Sequence

from core.errors import ApplicationError
from core.logger import setup_logger

from data.base import MarketDataProvider
from data.models import Candle


logger = setup_logger()


class DataManager:
    """Central orchestration layer for market-data providers.

    This class owns provider registration and selection, request validation,
    candle normalization, and the explicit multi-provider fallback API.

    Provider-specific API details stay inside the concrete providers and the
    ProviderManager layer. The rest of the application only sees Candle data.
    """

    DEFAULT_LIMIT = MarketDataProvider.DEFAULT_LIMIT
    MAX_LIMIT = MarketDataProvider.MAX_LIMIT

    def __init__(self, default_provider: str | None = None) -> None:
        if default_provider is not None:
            default_provider = self._normalize_provider_name(default_provider)

        self.providers: dict[str, MarketDataProvider] = {}
        self.default_provider = default_provider

    # ------------------------------------------------------------------
    # Provider registration
    # ------------------------------------------------------------------

    def register(self, provider: MarketDataProvider) -> None:
        """Register one provider and assign the first provider as default."""
        if not isinstance(provider, MarketDataProvider):
            raise TypeError(
                "provider must implement MarketDataProvider."
            )

        name = getattr(provider, "name", None)
        if not isinstance(name, str):
            raise TypeError("provider.name must be a string.")

        name = self._normalize_provider_name(name)

        if name in self.providers:
            raise ApplicationError(
                f"Provider already registered: {name}"
            )

        self.providers[name] = provider

        if self.default_provider is None:
            self.default_provider = name

        logger.info(
            "Market data provider registered: %s",
            name,
        )

    def unregister(self, name: str) -> None:
        """Remove a provider and repair the default-provider selection."""
        normalized_name = self._normalize_provider_name(name)

        if normalized_name not in self.providers:
            raise ApplicationError(
                f"Market data provider not found: {normalized_name}"
            )

        del self.providers[normalized_name]

        if self.default_provider == normalized_name:
            self.default_provider = next(
                iter(self.providers),
                None,
            )

        logger.info(
            "Market data provider removed: %s",
            normalized_name,
        )

    # ------------------------------------------------------------------
    # Provider lookup
    # ------------------------------------------------------------------

    def has_provider(self, name: str) -> bool:
        """Return whether a provider is registered."""
        normalized_name = self._normalize_provider_name(name)
        return normalized_name in self.providers

    def get_provider(self, name: str) -> MarketDataProvider:
        """Return a registered provider or raise an application error."""
        normalized_name = self._normalize_provider_name(name)
        provider = self.providers.get(normalized_name)

        if provider is None:
            raise ApplicationError(
                f"Market data provider not found: {normalized_name}"
            )

        return provider

    # ------------------------------------------------------------------
    # Default provider
    # ------------------------------------------------------------------

    def set_default_provider(self, name: str) -> None:
        """Set an already registered provider as the default."""
        normalized_name = self._normalize_provider_name(name)

        if normalized_name not in self.providers:
            raise ApplicationError(
                f"Cannot set unknown provider as default: {normalized_name}"
            )

        self.default_provider = normalized_name

        logger.info(
            "Default market data provider set to: %s",
            normalized_name,
        )

    def get_default_provider(self) -> MarketDataProvider:
        """Return the configured default provider."""
        if not self.default_provider:
            raise ApplicationError(
                "No default market data provider has been configured."
            )

        return self.get_provider(self.default_provider)

    # ------------------------------------------------------------------
    # Candle retrieval
    # ------------------------------------------------------------------

    async def get_candles(
        self,
        provider_name: str | None,
        symbol: str,
        timeframe: str,
        limit: int = DEFAULT_LIMIT,
    ) -> list[Candle]:
        """Fetch candles from one selected provider.

        Provider output is normalized into a deterministic chronological
        sequence before it crosses this layer's boundary.
        """
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

        logger.info(
            "Fetched %d candles for %s from %s.",
            len(normalized),
            symbol,
            provider.name,
        )

        return normalized

    # ------------------------------------------------------------------
    # Explicit fallback
    # ------------------------------------------------------------------

    async def get_candles_with_fallback(
        self,
        symbol: str,
        timeframe: str,
        limit: int = DEFAULT_LIMIT,
        providers: Sequence[str] | None = None,
    ) -> list[Candle]:
        """Try providers in order until one returns usable candles.

        An empty result is treated as an unsuccessful provider response so
        that the next provider can be attempted.
        """
        symbol, timeframe, limit = self._validate_request(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

        if providers is None:
            provider_names = list(self.providers)
        else:
            provider_names = [
                self._normalize_provider_name(name)
                for name in providers
            ]

        if not provider_names:
            raise ApplicationError(
                "No market data providers are available."
            )

        errors: dict[str, str] = {}

        for provider_name in provider_names:
            provider = self.providers.get(provider_name)
            if provider is None:
                errors[provider_name] = "Provider is not registered."
                logger.warning(
                    "Fallback provider is not registered: %s",
                    provider_name,
                )
                continue

            try:
                candles = await provider.get_candles(
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=limit,
                )
                normalized = self._normalize_candles(
                    candles,
                    symbol=symbol,
                    limit=limit,
                )

                if not normalized:
                    raise ValueError("Provider returned no candles.")

                logger.info(
                    "Market data successfully retrieved using provider: %s",
                    provider_name,
                )
                return normalized

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

    # ------------------------------------------------------------------
    # Provider information
    # ------------------------------------------------------------------

    def list_providers(self) -> list[str]:
        """Return registered provider names in registration order."""
        return list(self.providers)

    def provider_count(self) -> int:
        """Return the number of registered providers."""
        return len(self.providers)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_provider_name(name: str) -> str:
        if not isinstance(name, str):
            raise TypeError("Provider name must be a string.")

        normalized = name.strip().lower()
        if not normalized:
            raise ValueError("Provider name cannot be empty.")

        return normalized

    @classmethod
    def _validate_request(
        cls,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> tuple[str, str, int]:
        """Validate and normalize the common market-data request."""
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string.")

        symbol = symbol.strip().upper()
        if not symbol:
            raise ValueError("symbol cannot be empty.")

        if not isinstance(timeframe, str):
            raise TypeError("timeframe must be a string.")

        timeframe = MarketDataProvider.normalize_timeframe(timeframe)

        if isinstance(limit, bool) or not isinstance(limit, int):
            raise TypeError("limit must be an integer.")

        if limit < 1:
            raise ValueError("limit must be greater than zero.")

        if limit > cls.MAX_LIMIT:
            raise ValueError(
                f"limit cannot exceed {cls.MAX_LIMIT}."
            )

        return symbol, timeframe, limit

    @classmethod
    def _normalize_candles(
        cls,
        candles: list[Candle] | Sequence[Candle],
        *,
        symbol: str,
        limit: int,
    ) -> list[Candle]:
        """Validate, sort, deduplicate, and limit provider candle output."""
        if not isinstance(candles, list):
            raise TypeError("Provider must return a list of candles.")

        normalized = MarketDataProvider.normalize_candles(
            candles,
            expected_symbol=symbol,
            deduplicate=True,
        )

        return MarketDataProvider.apply_limit(
            normalized,
            limit,
        )


__all__ = ["DataManager"]
