from __future__ import annotations

from collections.abc import Mapping
from threading import RLock
from typing import TypeAlias

from core.errors import ApplicationError
from data.base import MarketDataProvider
from data.providers.alphavantage_provider import AlphaVantageProvider
from data.providers.finnhub_provider import FinnhubProvider
from data.providers.oanda_provider import OandaProvider


ProviderClass: TypeAlias = type[MarketDataProvider]


class ProviderFactory:
    """
    Central factory for market-data providers.

    Responsibilities:
    - Register available providers.
    - Create providers by name.
    - Normalize provider names.
    - Support provider aliases.
    - Expose available providers.
    - Allow future runtime registration.
    - Keep backward compatibility with the existing project API.

    Existing usage remains valid:

        ProviderFactory.create("oanda")
        ProviderFactory.create("finnhub")
        ProviderFactory.create("alphavantage")

        ProviderFactory.available()
    """

    # ------------------------------------------------------------------
    # Built-in providers
    # ------------------------------------------------------------------

    _providers: dict[str, ProviderClass] = {
        "oanda": OandaProvider,
        "finnhub": FinnhubProvider,
        "alphavantage": AlphaVantageProvider,
    }

    # ------------------------------------------------------------------
    # Aliases
    #
    # These do not replace the original provider names.
    # They simply make provider selection more flexible.
    # ------------------------------------------------------------------

    _aliases: dict[str, str] = {
        "oanda": "oanda",
        "oanda-api": "oanda",
        "oanda_api": "oanda",

        "finnhub": "finnhub",
        "finnhub-api": "finnhub",
        "finnhub_api": "finnhub",

        "alphavantage": "alphavantage",
        "alpha-vantage": "alphavantage",
        "alpha_vantage": "alphavantage",
        "alphavantage-api": "alphavantage",
        "alphavantage_api": "alphavantage",
    }

    # ------------------------------------------------------------------
    # Thread safety
    # ------------------------------------------------------------------

    _lock = RLock()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_name(provider_name: str) -> str:
        """
        Normalize a provider name.

        Examples:

            " OANDA "       -> "oanda"
            "FinnHub"       -> "finnhub"
            "alpha-vantage" -> "alpha-vantage"
        """

        if not isinstance(provider_name, str):
            raise TypeError(
                "provider_name must be a string."
            )

        normalized = provider_name.strip().lower()

        if not normalized:
            raise ApplicationError(
                "Provider name cannot be empty.",
                {
                    "provider": provider_name,
                },
            )

        return normalized

    @classmethod
    def _resolve_name(cls, provider_name: str) -> str:
        """
        Resolve a provider name or alias to its canonical name.
        """

        normalized_name = cls._normalize_name(
            provider_name
        )

        with cls._lock:
            canonical_name = cls._aliases.get(
                normalized_name
            )

            if canonical_name is not None:
                return canonical_name

            if normalized_name in cls._providers:
                return normalized_name

        raise ApplicationError(
            "Unknown market data provider.",
            {
                "provider": provider_name,
                "normalized": normalized_name,
                "available": cls.available(),
            },
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
        Create a market-data provider instance by name.

        Backward-compatible examples:

            ProviderFactory.create("oanda")
            ProviderFactory.create("finnhub")
            ProviderFactory.create("alphavantage")

        Aliases are also accepted.
        """

        canonical_name = cls._resolve_name(
            provider_name
        )

        with cls._lock:
            provider_class = cls._providers.get(
                canonical_name
            )

        if provider_class is None:
            raise ApplicationError(
                "Provider is registered but unavailable.",
                {
                    "provider": provider_name,
                    "canonical_name": canonical_name,
                    "available": cls.available(),
                },
            )

        try:
            provider = provider_class()
        except ApplicationError:
            raise
        except Exception as exc:
            raise ApplicationError(
                "Failed to initialize market data provider.",
                {
                    "provider": canonical_name,
                    "error": str(exc),
                },
            ) from exc

        if not isinstance(
            provider,
            MarketDataProvider,
        ):
            raise ApplicationError(
                "Registered provider is not a valid "
                "MarketDataProvider.",
                {
                    "provider": canonical_name,
                    "class": provider_class.__name__,
                },
            )

        return provider

    # ------------------------------------------------------------------
    # Provider registration
    # ------------------------------------------------------------------

    @classmethod
    def register(
        cls,
        name: str,
        provider_class: ProviderClass,
        *,
        aliases: tuple[str, ...] = (),
        overwrite: bool = False,
    ) -> None:
        """
        Register a provider dynamically.

        This gives us a clean extension point for future providers
        without modifying the factory itself.

        Example:

            ProviderFactory.register(
                "new_provider",
                NewProvider,
                aliases=("new-api",),
            )
        """

        canonical_name = cls._normalize_name(name)

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

        normalized_aliases = tuple(
            cls._normalize_name(alias)
            for alias in aliases
        )

        with cls._lock:
            if (
                canonical_name in cls._providers
                and not overwrite
            ):
                raise ApplicationError(
                    "Provider is already registered.",
                    {
                        "provider": canonical_name,
                    },
                )

            cls._providers[
                canonical_name
            ] = provider_class

            cls._aliases[
                canonical_name
            ] = canonical_name

            for alias in normalized_aliases:
                existing_target = cls._aliases.get(
                    alias
                )

                if (
                    existing_target is not None
                    and existing_target != canonical_name
                ):
                    raise ApplicationError(
                        "Provider alias is already registered.",
                        {
                            "alias": alias,
                            "existing_provider": existing_target,
                            "provider": canonical_name,
                        },
                    )

                cls._aliases[
                    alias
                ] = canonical_name

    # ------------------------------------------------------------------
    # Provider removal
    # ------------------------------------------------------------------

    @classmethod
    def unregister(
        cls,
        provider_name: str,
    ) -> bool:
        """
        Remove a dynamically registered provider.

        Returns:
            True  -> provider was removed
            False -> provider did not exist

        Built-in providers are not protected at this layer,
        but unregistering one should only be done deliberately.
        """

        canonical_name = cls._normalize_name(
            provider_name
        )

        with cls._lock:
            if canonical_name not in cls._providers:
                return False

            del cls._providers[
                canonical_name
            ]

            aliases_to_remove = [
                alias
                for alias, target in cls._aliases.items()
                if target == canonical_name
            ]

            for alias in aliases_to_remove:
                del cls._aliases[alias]

        return True

    # ------------------------------------------------------------------
    # Provider inspection
    # ------------------------------------------------------------------

    @classmethod
    def available(cls) -> list[str]:
        """
        Return canonical names of available providers.

        The original method is intentionally preserved.
        """

        with cls._lock:
            return list(
                cls._providers.keys()
            )

    @classmethod
    def aliases(cls) -> dict[str, str]:
        """
        Return a copy of the provider alias mapping.
        """

        with cls._lock:
            return dict(
                cls._aliases
            )

    @classmethod
    def is_available(
        cls,
        provider_name: str,
    ) -> bool:
        """
        Check whether a provider or alias is registered.
        """

        try:
            cls._resolve_name(
                provider_name
            )
        except (
            TypeError,
            ApplicationError,
        ):
            return False

        return True

    @classmethod
    def get_provider_class(
        cls,
        provider_name: str,
    ) -> ProviderClass:
        """
        Return the registered provider class without
        instantiating it.
        """

        canonical_name = cls._resolve_name(
            provider_name
        )

        with cls._lock:
            provider_class = cls._providers.get(
                canonical_name
            )

        if provider_class is None:
            raise ApplicationError(
                "Provider is unavailable.",
                {
                    "provider": canonical_name,
                },
            )

        return provider_class

    @classmethod
    def snapshot(cls) -> Mapping[str, ProviderClass]:
        """
        Return a read-only-style snapshot of the current
        provider registry.

        A normal dict copy is returned so callers cannot mutate
        the internal registry accidentally.
        """

        with cls._lock:
            return dict(
                cls._providers
            )


__all__ = [
    "ProviderFactory",
    "ProviderClass",
]
