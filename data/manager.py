from __future__ import annotations

from collections.abc import Sequence

from core.errors import ApplicationError
from core.logger import setup_logger

from data.base import MarketDataProvider
from data.models import Candle


logger = setup_logger()


class DataManager:
    """
    Central market-data orchestration layer.

    Responsibilities:

    - Register market-data providers.
    - Manage the default provider.
    - Select providers explicitly.
    - Fetch normalized Candle objects.
    - Support provider fallback.
    - Validate request parameters.
    - Expose provider-management utilities.
    """

    def __init__(
        self,
        default_provider: str | None = None,
    ) -> None:

        self.providers: dict[
            str,
            MarketDataProvider,
        ] = {}

        self.default_provider = (
            default_provider
        )

    # ---------------------------------------------------------
    # Provider registration
    # ---------------------------------------------------------

    def register(
        self,
        provider: MarketDataProvider,
    ) -> None:
        """
        Register a market-data provider.
        """

        if not isinstance(
            provider,
            MarketDataProvider,
        ):
            raise TypeError(
                "provider must implement "
                "MarketDataProvider."
            )

        name = (
            provider.name
            if isinstance(
                provider.name,
                str,
            )
            else ""
        )

        name = name.strip().lower()

        if not name:
            raise ApplicationError(
                "Provider name cannot be empty."
            )

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

    def unregister(
        self,
        name: str,
    ) -> None:
        """
        Remove a registered provider.
        """

        normalized_name = self._normalize_provider_name(
            name
        )

        if normalized_name not in self.providers:
            raise ApplicationError(
                f"Market data provider not found: "
                f"{normalized_name}"
            )

        del self.providers[
            normalized_name
        ]

        if (
            self.default_provider
            == normalized_name
        ):
            self.default_provider = (
                next(
                    iter(
                        self.providers
                    ),
                    None,
                )
            )

        logger.info(
            "Market data provider removed: %s",
            normalized_name,
        )

    # ---------------------------------------------------------
    # Provider lookup
    # ---------------------------------------------------------

    def has_provider(
        self,
        name: str,
    ) -> bool:
        """
        Check whether a provider is registered.
        """

        normalized_name = (
            self._normalize_provider_name(
                name
            )
        )

        return (
            normalized_name
            in self.providers
        )

    def get_provider(
        self,
        name: str,
    ) -> MarketDataProvider:
        """
        Return a registered provider.
        """

        normalized_name = (
            self._normalize_provider_name(
                name
            )
        )

        provider = self.providers.get(
            normalized_name
        )

        if provider is None:
            raise ApplicationError(
                f"Market data provider not found: "
                f"{normalized_name}"
            )

        return provider

    # ---------------------------------------------------------
    # Default provider
    # ---------------------------------------------------------

    def set_default_provider(
        self,
        name: str,
    ) -> None:
        """
        Set the default market-data provider.
        """

        normalized_name = (
            self._normalize_provider_name(
                name
            )
        )

        if normalized_name not in self.providers:
            raise ApplicationError(
                f"Cannot set unknown provider "
                f"as default: {normalized_name}"
            )

        self.default_provider = (
            normalized_name
        )

        logger.info(
            "Default market data provider set to: %s",
            normalized_name,
        )

    def get_default_provider(
        self,
    ) -> MarketDataProvider:
        """
        Return the default provider.
        """

        if not self.default_provider:
            raise ApplicationError(
                "No default market data provider "
                "has been configured."
            )

        return self.get_provider(
            self.default_provider
        )

    # ---------------------------------------------------------
    # Candle retrieval
    # ---------------------------------------------------------

    async def get_candles(
        self,
        provider_name: str | None,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> list[Candle]:
        """
        Fetch candles from a selected provider.

        If provider_name is None, the default provider
        is used.
        """

        self._validate_request(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

        if provider_name is None:
            provider = (
                self.get_default_provider()
            )
        else:
            provider = self.get_provider(
                provider_name
            )

        try:
            candles = await provider.get_candles(
                symbol=symbol,
                timeframe=timeframe,
                limit=limit,
            )

        except Exception as error:
            logger.exception(
                "Market data request failed. "
                "Provider=%s Symbol=%s Timeframe=%s",
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

        if not isinstance(
            candles,
            list,
        ):
            raise ApplicationError(
                "Provider returned invalid candle data.",
                {
                    "provider": provider.name,
                    "symbol": symbol,
                },
            )

        logger.info(
            "Fetched %d candles for %s "
            "from %s.",
            len(candles),
            symbol,
            provider.name,
        )

        return candles

    # ---------------------------------------------------------
    # Fallback
    # ---------------------------------------------------------

    async def get_candles_with_fallback(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
        providers: Sequence[str] | None = None,
    ) -> list[Candle]:
        """
        Fetch candles using multiple providers.

        Providers are tried in the supplied order.

        If no provider list is supplied,
        registered providers are used in registration order.
        """

        self._validate_request(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

        if providers is None:
            provider_names = list(
                self.providers.keys()
            )
        else:
            provider_names = [
                self._normalize_provider_name(
                    name
                )
                for name in providers
            ]

        if not provider_names:
            raise ApplicationError(
                "No market data providers are available."
            )

        errors: dict[
            str,
            str,
        ] = {}

        for provider_name in provider_names:

            if not self.has_provider(
                provider_name
            ):
                errors[
                    provider_name
                ] = "Provider is not registered."

                logger.warning(
                    "Fallback provider is not registered: %s",
                    provider_name,
                )

                continue

            provider = self.get_provider(
                provider_name
            )

            try:
                candles = await provider.get_candles(
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=limit,
                )

                if not isinstance(
                    candles,
                    list,
                ):
                    raise TypeError(
                        "Provider returned "
                        "non-list candle data."
                    )

                if not candles:
                    raise ValueError(
                        "Provider returned no candles."
                    )

                logger.info(
                    "Market data successfully "
                    "retrieved using provider: %s",
                    provider_name,
                )

                return candles

            except Exception as error:

                errors[
                    provider_name
                ] = str(error)

                logger.exception(
                    "Provider failed during fallback: %s",
                    provider_name,
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

    # ---------------------------------------------------------
    # Provider information
    # ---------------------------------------------------------

    def list_providers(
        self,
    ) -> list[str]:
        """
        Return registered provider names.
        """

        return list(
            self.providers.keys()
        )

    def provider_count(
        self,
    ) -> int:
        """
        Return the number of registered providers.
        """

        return len(
            self.providers
        )

    # ---------------------------------------------------------
    # Internal validation
    # ---------------------------------------------------------

    @staticmethod
    def _normalize_provider_name(
        name: str,
    ) -> str:
        """
        Normalize a provider name.
        """

        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "Provider name must be a string."
            )

        normalized = name.strip().lower()

        if not normalized:
            raise ValueError(
                "Provider name cannot be empty."
            )

        return normalized

    @staticmethod
    def _validate_request(
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> None:
        """
        Validate a market-data request.
        """

        if not isinstance(
            symbol,
            str,
        ):
            raise TypeError(
                "symbol must be a string."
            )

        if not symbol.strip():
            raise ValueError(
                "symbol cannot be empty."
            )

        if not isinstance(
            timeframe,
            str,
        ):
            raise TypeError(
                "timeframe must be a string."
            )

        if not timeframe.strip():
            raise ValueError(
                "timeframe cannot be empty."
            )

        if not isinstance(
            limit,
            int,
        ):
            raise TypeError(
                "limit must be an integer."
            )

        if limit < 1:
            raise ValueError(
                "limit must be greater than zero."
            )
