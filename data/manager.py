from __future__ import annotations

from data.base import MarketDataProvider
from data.models import Candle

from core.errors import ApplicationError
from core.logger import setup_logger


logger = setup_logger()


class DataManager:
    """
    Central manager for market data providers.
    """

    def __init__(self) -> None:
        self.providers: dict[
            str,
            MarketDataProvider,
        ] = {}

    def register(
        self,
        provider: MarketDataProvider,
    ) -> None:
        """
        Register a market data provider.
        """

        if not provider.name:
            raise ApplicationError(
                "Provider name cannot be empty."
            )

        if provider.name in self.providers:
            raise ApplicationError(
                f"Provider already registered: "
                f"{provider.name}"
            )

        self.providers[
            provider.name
        ] = provider

        logger.info(
            "Market data provider registered: %s",
            provider.name,
        )

    def get_provider(
        self,
        name: str,
    ) -> MarketDataProvider:
        """
        Return a registered provider.
        """

        provider = self.providers.get(
            name
        )

        if provider is None:
            raise ApplicationError(
                f"Market data provider not found: "
                f"{name}"
            )

        return provider

    async def get_candles(
        self,
        provider_name: str,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> list[Candle]:
        """
        Fetch candles from selected provider.
        """

        if limit < 1:
            raise ValueError(
                "limit must be greater than zero."
            )

        provider = self.get_provider(
            provider_name
        )

        candles = await provider.get_candles(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

        logger.info(
            "Fetched %d candles for %s "
            "from %s.",
            len(candles),
            symbol,
            provider_name,
        )

        return candles

    def list_providers(self) -> list[str]:
        """
        Return registered provider names.
        """

        return list(
            self.providers.keys()
        )
