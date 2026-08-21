from __future__ import annotations

from data.base import MarketDataProvider

from data.providers.oanda_provider import OandaProvider
from data.providers.finnhub_provider import FinnhubProvider
from data.providers.alphavantage_provider import AlphaVantageProvider

from core.errors import ApplicationError


class ProviderFactory:
    """
    Factory for creating market data providers.
    """


    _providers: dict[str, type[MarketDataProvider]] = {
        "oanda": OandaProvider,
        "finnhub": FinnhubProvider,
        "alphavantage": AlphaVantageProvider,
    }


    @classmethod
    def create(
        cls,
        provider_name: str,
    ) -> MarketDataProvider:
        """
        Create provider instance by name.
        """

        if not isinstance(
            provider_name,
            str,
        ):
            raise TypeError(
                "provider_name must be a string."
            )


        normalized_name = (
            provider_name
            .strip()
            .lower()
        )


        provider_class = cls._providers.get(
            normalized_name
        )


        if provider_class is None:
            raise ApplicationError(
                "Unknown market data provider.",
                {
                    "provider": provider_name,
                    "available": list(
                        cls._providers.keys()
                    ),
                },
            )


        return provider_class()


    @classmethod
    def available(
        cls,
    ) -> list[str]:
        """
        Return available providers.
        """

        return list(
            cls._providers.keys()
        )
