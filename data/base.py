from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Final

from data.models import Candle


class MarketDataProviderError(Exception):
    """
    Base exception for market-data provider errors.
    """


class ProviderConfigurationError(MarketDataProviderError):
    """
    Raised when a provider is not configured correctly.
    """


class ProviderConnectionError(MarketDataProviderError):
    """
    Raised when a provider cannot be reached.
    """


class ProviderResponseError(MarketDataProviderError):
    """
    Raised when a provider returns invalid or unusable data.
    """


class InvalidMarketDataRequest(MarketDataProviderError):
    """
    Raised when a market-data request is invalid.
    """


class MarketDataProvider(ABC):
    """
    Base contract for all market-data providers.

    All providers such as:
        - OANDA
        - Finnhub
        - AlphaVantage
        - future providers

    must implement get_candles() and expose a provider name.

    Backward compatibility:
        The existing project already uses:

            provider.name
            provider.get_candles(...)

        so those interfaces are intentionally preserved.
    """

    # ------------------------------------------------------------------
    # Provider metadata
    # ------------------------------------------------------------------

    name: str = "unknown"

    # Maximum number of candles accepted by the generic interface.
    # Individual providers may impose stricter limits.
    MAX_LIMIT: Final[int] = 5000

    # ------------------------------------------------------------------
    # Core interface
    # ------------------------------------------------------------------

    @abstractmethod
    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> list[Candle]:
        """
        Fetch standardized market candles.

        Parameters
        ----------
        symbol:
            Market symbol, e.g. EURUSD.

        timeframe:
            Candle timeframe, e.g. 1m, 5m, 15m, 1h, 4h, 1d.

        limit:
            Number of candles requested.

        Returns
        -------
        list[Candle]
            Provider-independent candle objects.
        """

        raise NotImplementedError

    # ------------------------------------------------------------------
    # Provider status
    # ------------------------------------------------------------------

    def is_configured(self) -> bool:
        """
        Return whether this provider is configured and usable.

        The default implementation assumes the provider is configured.

        Providers that require API credentials can override this method.
        """

        return True

    async def health_check(self) -> bool:
        """
        Check whether the provider is currently healthy.

        The default implementation only checks configuration.

        Concrete providers can override this method when they have a
        lightweight API health endpoint or connection check.
        """

        return self.is_configured()

    # ------------------------------------------------------------------
    # Request validation
    # ------------------------------------------------------------------

    @classmethod
    def validate_symbol(cls, symbol: str) -> str:
        """
        Validate and normalize a market symbol.

        Examples:
            EURUSD
            eurusd -> EURUSD
            " EURUSD " -> EURUSD
        """

        if not isinstance(symbol, str):
            raise InvalidMarketDataRequest(
                "symbol must be a string."
            )

        normalized = symbol.strip().upper()

        if not normalized:
            raise InvalidMarketDataRequest(
                "symbol cannot be empty."
            )

        if len(normalized) > 30:
            raise InvalidMarketDataRequest(
                "symbol is too long."
            )

        return normalized

    @classmethod
    def validate_timeframe(cls, timeframe: str) -> str:
        """
        Validate and normalize a timeframe.

        Supported common formats include:

            1m
            5m
            15m
            30m
            1h
            2h
            4h
            6h
            8h
            12h
            1d
            1w
            1M
        """

        if not isinstance(timeframe, str):
            raise InvalidMarketDataRequest(
                "timeframe must be a string."
            )

        normalized = timeframe.strip()

        if not normalized:
            raise InvalidMarketDataRequest(
                "timeframe cannot be empty."
            )

        if len(normalized) > 10:
            raise InvalidMarketDataRequest(
                "timeframe is invalid."
            )

        # Keep "M" distinct from "m":
        # m = minute
        # M = month
        if normalized.endswith("M"):
            unit = "M"
            value = normalized[:-1]
        else:
            unit = normalized[-1:].lower()
            value = normalized[:-1]

        valid_units = {"m", "h", "d", "w"}

        if unit not in valid_units and normalized[-1:] != "M":
            raise InvalidMarketDataRequest(
                f"Unsupported timeframe: {timeframe!r}"
            )

        if not value.isdigit():
            raise InvalidMarketDataRequest(
                f"Invalid timeframe: {timeframe!r}"
            )

        amount = int(value)

        if amount <= 0:
            raise InvalidMarketDataRequest(
                f"Timeframe must be greater than zero: {timeframe!r}"
            )

        return normalized

    @classmethod
    def validate_limit(
        cls,
        limit: int,
        *,
        default: int = 100,
    ) -> int:
        """
        Validate the requested candle count.
        """

        if limit is None:
            limit = default

        if isinstance(limit, bool):
            raise InvalidMarketDataRequest(
                "limit must be an integer."
            )

        if not isinstance(limit, int):
            raise InvalidMarketDataRequest(
                "limit must be an integer."
            )

        if limit <= 0:
            raise InvalidMarketDataRequest(
                "limit must be greater than zero."
            )

        if limit > cls.MAX_LIMIT:
            raise InvalidMarketDataRequest(
                f"limit cannot exceed {cls.MAX_LIMIT}."
            )

        return limit

    @classmethod
    def validate_request(
        cls,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> tuple[str, str, int]:
        """
        Validate a complete candle request.

        Returns
        -------
        tuple[str, str, int]
            Normalized symbol, timeframe and validated limit.
        """

        normalized_symbol = cls.validate_symbol(symbol)
        normalized_timeframe = cls.validate_timeframe(timeframe)
        normalized_limit = cls.validate_limit(limit)

        return (
            normalized_symbol,
            normalized_timeframe,
            normalized_limit,
        )

    # ------------------------------------------------------------------
    # Result validation
    # ------------------------------------------------------------------

    @classmethod
    def validate_candles(
        cls,
        candles: list[Candle],
    ) -> list[Candle]:
        """
        Validate the result returned by a provider.

        The Candle model itself performs the detailed OHLC validation.
        Here we validate the collection and its elements.
        """

        if not isinstance(candles, list):
            raise ProviderResponseError(
                "Provider result must be a list of Candle objects."
            )

        for candle in candles:
            if not isinstance(candle, Candle):
                raise ProviderResponseError(
                    "Provider returned an invalid candle object."
                )

        return candles

    # ------------------------------------------------------------------
    # Provider information
    # ------------------------------------------------------------------

    @property
    def provider_name(self) -> str:
        """
        Return the normalized provider name.

        This is an additional convenience API and does not replace
        the existing `name` attribute.
        """

        value = getattr(self, "name", None)

        if not isinstance(value, str) or not value.strip():
            return self.__class__.__name__

        return value.strip()

    def __repr__(self) -> str:
        """
        Developer-friendly provider representation.
        """

        return (
            f"{self.__class__.__name__}"
            f"(name={self.provider_name!r})"
        )


__all__ = [
    "MarketDataProvider",
    "MarketDataProviderError",
    "ProviderConfigurationError",
    "ProviderConnectionError",
    "ProviderResponseError",
    "InvalidMarketDataRequest",
]
