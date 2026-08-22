
from __future__ import annotations

from collections.abc import Mapping
from typing import Final

from core.errors import ApplicationError
from data.base import MarketDataProvider
from data.providers.alphavantage_provider import AlphaVantageProvider
from data.providers.finnhub_provider import FinnhubProvider
from data.providers.oanda_provider import OandaProvider


class ProviderFactory:
    """
    Central factory and registry for market-data providers.

    The factory provides a single stable entry point for creating
    market-data providers while keeping the concrete implementations
    isolated from the rest of the application.

    Existing API remains compatible:

        ProviderFactory.create("oanda")
        ProviderFactory.create("finnhub")
        ProviderFactory.create("alphavantage")

    New providers can be registered dynamically without changing the
    factory's core creation logic.
    """

    # ------------------------------------------------------------------
    # Provider registry
    # ------------------------------------------------------------------

    _providers: dict[
        str,
        type[MarketDataProvider],
    ] = {
        "oanda": OandaProvider,
        "finnhub": FinnhubProvider,
        "alphavantage": AlphaVantageProvider,
    }

    # ------------------------------------------------------------------
    # Provider aliases
    #
    # These aliases are normalized into canonical provider names.
    # ------------------------------------------------------------------

    _aliases: Final[
        dict[str, str]
    ] = {
        "oanda": "oanda",

        "finnhub": "finnhub",

        "alphavantage": "alphavantage",
        "alpha_vantage": "alphavantage",
        "alpha-vantage": "alphavantage",
        "alpha vantage": "alphavantage",
    }

    # ------------------------------------------------------------------
    # Default provider
    # ------------------------------------------------------------------

    _default_provider: str = "oanda"

    # ------------------------------------------------------------------
    # Name normalization
    # ------------------------------------------------------------------

    @classmethod
    def normalize_name(
        cls,
        provider_name: str,
    ) -> str:
        """
        Normalize a provider name into its canonical name.

        Examples:

            " OANDA "       -> "oanda"
            "FinnHub"       -> "finnhub"
            "Alpha-Vantage" -> "alphavantage"
            "alpha_vantage" -> "alphavantage"
        """

        if not isinstance(
            provider_name,
            str,
        ):
            raise TypeError(
                "provider_name must be a string."
            )

        normalized = (
            provider_name
            .strip()
            .lower()
        )

        if not normalized:
            raise ValueError(
                "provider_name cannot be empty."
            )

        return cls._aliases.get(
            normalized,
            normalized,
        )

    # ------------------------------------------------------------------
    # Provider creation
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        provider_name: str,
    ) -> MarketDataProvider:
        """
        Create a market-data provider instance.

        Provider names are normalized before lookup.

        Raises:
            TypeError:
                provider_name is not a string.

            ValueError:
                provider_name is empty.

            ApplicationError:
                Provider is not registered.
        """

        normalized_name = cls.normalize_name(
            provider_name
        )

        provider_class = cls._providers.get(
            normalized_name
        )

        if provider_class is None:
            raise ApplicationError(
                "Unknown market data provider.",
                {
                    "provider": provider_name,
                    "normalized_provider": normalized_name,
                    "available": cls.available(),
                },
            )

        try:
            provider = provider_class()
        except Exception as exc:
            raise ApplicationError(
                "Failed to initialize market data provider.",
                {
                    "provider": normalized_name,
                    "provider_class": provider_class.__name__,
                    "error": str(exc),
                },
            ) from exc

        if not isinstance(
            provider,
            MarketDataProvider,
        ):
            raise ApplicationError(
                "Registered provider does not implement "
                "MarketDataProvider.",
                {
                    "provider": normalized_name,
                    "provider_class": provider_class.__name__,
                },
            )

        return provider

    # ------------------------------------------------------------------
    # Default provider
    # ------------------------------------------------------------------

    @classmethod
    def create_default(
        cls,
    ) -> MarketDataProvider:
        """
        Create the configured default provider.

        The default currently remains OANDA for backward compatibility.
        """

        return cls.create(
            cls._default_provider
        )

    @classmethod
    def default_name(
        cls,
    ) -> str:
        """
        Return the canonical name of the default provider.
        """

        return cls._default_provider

    @classmethod
    def set_default(
        cls,
        provider_name: str,
    ) -> None:
        """
        Change the default provider.

        The provider must already be registered.
        """

        normalized_name = cls.normalize_name(
            provider_name
        )

        if normalized_name not in cls._providers:
            raise ApplicationError(
                "Cannot set an unregistered provider "
                "as the default provider.",
                {
                    "provider": provider_name,
                    "available": cls.available(),
                },
            )

        cls._default_provider = normalized_name

    # ------------------------------------------------------------------
    # Registry management
    # ------------------------------------------------------------------

    @classmethod
    def register(
        cls,
        provider_name: str,
        provider_class: type[MarketDataProvider],
        *,
        overwrite: bool = False,
    ) -> None:
        """
        Register a new market-data provider.

        Example:

            ProviderFactory.register(
                "my_provider",
                MyProvider,
            )

        By default an existing provider cannot be overwritten.
        Set overwrite=True when intentional replacement is required.
        """

        normalized_name = cls.normalize_name(
            provider_name
        )

        if not isinstance(
            provider_class,
            type,
        ):
            raise TypeError(
                "provider_class must be a class."
            )

        if not issubclass(
            provider_class,
            MarketDataProvider,
        ):
            raise TypeError(
                "provider_class must inherit from "
                "MarketDataProvider."
            )

        if (
            normalized_name in cls._providers
            and not overwrite
        ):
            raise ApplicationError(
                "Provider is already registered.",
                {
                    "provider": normalized_name,
                    "available": cls.available(),
                },
            )

        cls._providers[
            normalized_name
        ] = provider_class

        # A canonical provider name should always resolve
        # to itself.
        cls._aliases[
            normalized_name
        ] = normalized_name

    @classmethod
    def unregister(
        cls,
        provider_name: str,
    ) -> None:
        """
        Remove a registered provider.

        The default provider cannot be removed until another
        default provider has been selected.
        """

        normalized_name = cls.normalize_name(
            provider_name
        )

        if normalized_name not in cls._providers:
            raise ApplicationError(
                "Provider is not registered.",
                {
                    "provider": normalized_name,
                    "available": cls.available(),
                },
            )

        if (
            normalized_name
            == cls._default_provider
        ):
            raise ApplicationError(
                "Cannot unregister the default provider.",
                {
                    "provider": normalized_name,
                    "default": cls._default_provider,
                },
            )

        del cls._providers[
            normalized_name
        ]

        # Remove aliases pointing to the provider.
        aliases_to_remove = [
            alias
            for alias, target
            in cls._aliases.items()
            if target == normalized_name
        ]

        for alias in aliases_to_remove:
            del cls._aliases[
                alias
            ]

    # ------------------------------------------------------------------
    # Provider lookup
    # ------------------------------------------------------------------

    @classmethod
    def is_supported(
        cls,
        provider_name: str,
    ) -> bool:
        """
        Return True if a provider is registered.
        """

        if not isinstance(
            provider_name,
            str,
        ):
            return False

        try:
            normalized_name = cls.normalize_name(
                provider_name
            )
        except (
            TypeError,
            ValueError,
        ):
            return False

        return normalized_name in cls._providers

    @classmethod
    def get_provider_class(
        cls,
        provider_name: str,
    ) -> type[MarketDataProvider]:
        """
        Return the registered provider class without
        instantiating it.
        """

        normalized_name = cls.normalize_name(
            provider_name
        )

        provider_class = cls._providers.get(
            normalized_name
        )

        if provider_class is None:
            raise ApplicationError(
                "Unknown market data provider.",
                {
                    "provider": provider_name,
                    "available": cls.available(),
                },
            )

        return provider_class

    # ------------------------------------------------------------------
    # Provider availability
    # ------------------------------------------------------------------

    @classmethod
    def available(
        cls,
    ) -> list[str]:
        """
        Return all registered canonical provider names.

        A new list is returned so callers cannot accidentally
        mutate the internal registry.
        """

        return sorted(
            cls._providers.keys()
        )

    @classmethod
    def aliases(
        cls,
    ) -> Mapping[str, str]:
        """
        Return a read-only view of provider aliases.
        """

        return dict(
            cls._aliases
        )

    @classmethod
    def registry(
        cls,
    ) -> Mapping[
        str,
        type[MarketDataProvider],
    ]:
        """
        Return a snapshot of the current provider registry.

        The returned dictionary is a copy and cannot directly
        mutate the internal registry.
        """

        return dict(
            cls._providers
        )

    # ------------------------------------------------------------------
    # Provider health/configuration
    # ------------------------------------------------------------------

    @classmethod
    def configured(
        cls,
        provider_name: str,
    ) -> bool:
        """
        Check whether a provider can be considered configured.

        This does not perform a network request.

        It only calls the provider's local is_configured()
        implementation.
        """

        provider = cls.create(
            provider_name
        )

        return bool(
            provider.is_configured()
        )

    @classmethod
    def configured_providers(
        cls,
    ) -> list[str]:
        """
        Return providers that are locally configured.

        No external API calls are performed.
        """

        result: list[str] = []

        for provider_name in cls.available():
            try:
                if cls.configured(
                    provider_name
                ):
                    result.append(
                        provider_name
                    )
            except Exception:
                # A provider that cannot be initialized is not
                # considered configured.
                continue

        return result


__all__ = [
    "ProviderFactory",
]

