
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from data.models import Candle


class MarketDataProvider(ABC):
    """
    Base contract for all market-data providers.

    Every provider in the project must implement this interface.

    The interface intentionally keeps the existing public API:

        provider.name
        await provider.get_candles(symbol, timeframe, limit)

    so existing providers and tests remain compatible.
    """

    # ------------------------------------------------------------------
    # Provider identity
    # ------------------------------------------------------------------

    name: str = "unknown"

    # ------------------------------------------------------------------
    # Provider capabilities
    # ------------------------------------------------------------------

    supports_historical: bool = True
    supports_realtime: bool = False

    # ------------------------------------------------------------------
    # Provider health / metadata
    # ------------------------------------------------------------------

    @property
    def provider_name(self) -> str:
        """
        Canonical provider name.

        Keeps `name` as the source of truth while providing a cleaner
        interface for future infrastructure.
        """
        return self.name

    @property
    def is_available(self) -> bool:
        """
        Whether the provider is currently considered available.

        Concrete providers can override this later if they implement
        health checks.
        """
        return True

    # ------------------------------------------------------------------
    # Core market-data API
    # ------------------------------------------------------------------

    @abstractmethod
    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> list[Candle]:
        """
        Fetch normalized OHLCV candles.

        Parameters
        ----------
        symbol:
            Market symbol, for example EURUSD.

        timeframe:
            Candle timeframe, for example 1m, 5m, 15m, 1h, 4h, 1d.

        limit:
            Maximum number of candles requested.

        Returns
        -------
        list[Candle]
            Provider-independent normalized candles.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Optional lifecycle
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        """
        Lightweight provider health check.

        Providers may override this when an actual API health endpoint
        or connectivity test is available.

        The default implementation deliberately does not perform
        network traffic.
        """
        return self.is_available

    async def close(self) -> None:
        """
        Optional asynchronous cleanup hook.

        HTTP clients, sessions, WebSocket connections, etc. can override
        this method later.

        The default implementation does nothing.
        """
        return None

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def validate_request(
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> None:
        """
        Validate common market-data request parameters.

        This is intentionally provider-independent so every provider
        follows the same basic rules.
        """

        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("symbol must be a non-empty string")

        if not isinstance(timeframe, str) or not timeframe.strip():
            raise ValueError("timeframe must be a non-empty string")

        if isinstance(limit, bool) or not isinstance(limit, int):
            raise TypeError("limit must be an integer")

        if limit <= 0:
            raise ValueError("limit must be greater than zero")

    # ------------------------------------------------------------------
    # Normalization helpers
    # ------------------------------------------------------------------

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        """
        Normalize a market symbol before sending it to a provider.

        This does NOT convert provider-specific formats.

        Example:

            " eurusd " -> "EURUSD"
        """
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")

        normalized = symbol.strip().upper()

        if not normalized:
            raise ValueError("symbol must not be empty")

        return normalized

    @staticmethod
    def normalize_timeframe(timeframe: str) -> str:
        """
        Normalize timeframe representation.

        Example:

            " 1H " -> "1h"
        """
        if not isinstance(timeframe, str):
            raise TypeError("timeframe must be a string")

        normalized = timeframe.strip().lower()

        if not normalized:
            raise ValueError("timeframe must not be empty")

        return normalized

    # ------------------------------------------------------------------
    # Provider information
    # ------------------------------------------------------------------

    def info(self) -> dict[str, Any]:
        """
        Return provider metadata.

        This gives the future Data Manager / Failover Manager a common
        way to inspect providers without knowing their concrete class.
        """
        return {
            "name": self.provider_name,
            "supports_historical": self.supports_historical,
            "supports_realtime": self.supports_realtime,
            "available": self.is_available,
        }

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(name={self.provider_name!r})"
        )


__all__ = [
    "MarketDataProvider",
]
