
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import datetime
from typing import Final

from data.models import Candle


class MarketDataProvider(ABC):
    """
    Common contract for all market-data providers.

    Every provider in the project must expose the same high-level API,
    regardless of the underlying service.

    Current providers:
        - OANDA
        - Finnhub
        - Alpha Vantage

    Future providers can implement this same contract without requiring
    changes in the analysis engine.
    """

    # ------------------------------------------------------------------
    # Provider metadata
    # ------------------------------------------------------------------

    name: str

    # Maximum number of candles accepted by the common contract.
    DEFAULT_LIMIT: Final[int] = 100
    MAX_LIMIT: Final[int] = 5000

    # ------------------------------------------------------------------
    # Main API
    # ------------------------------------------------------------------

    @abstractmethod
    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = DEFAULT_LIMIT,
    ) -> list[Candle]:
        """
        Fetch standardized market candles.

        Implementations MUST return:

            list[Candle]

        The returned candles should be:

        - provider-independent
        - timezone-aware
        - chronologically ordered
        - free of duplicate timestamps
        - valid according to Candle's constraints
        """

        raise NotImplementedError

    # ------------------------------------------------------------------
    # Provider status
    # ------------------------------------------------------------------

    def is_configured(self) -> bool:
        """
        Return whether the provider has the credentials/configuration
        required to communicate with its external service.

        Providers may override this method when they have custom
        configuration requirements.

        The default implementation assumes the provider is configured.
        """

        return True

    # ------------------------------------------------------------------
    # Request validation
    # ------------------------------------------------------------------

    @classmethod
    def validate_request(
        cls,
        symbol: str,
        timeframe: str,
        limit: int = DEFAULT_LIMIT,
    ) -> None:
        """
        Validate the common portion of a market-data request.

        Provider-specific timeframe validation should still happen
        inside the concrete provider.
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

        if isinstance(
            limit,
            bool,
        ):
            raise TypeError(
                "limit must be an integer."
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

        if limit > cls.MAX_LIMIT:
            raise ValueError(
                f"limit cannot exceed "
                f"{cls.MAX_LIMIT}."
            )

    # ------------------------------------------------------------------
    # Symbol normalization
    # ------------------------------------------------------------------

    @staticmethod
    def normalize_symbol(
        symbol: str,
    ) -> str:
        """
        Normalize a symbol without changing its semantic format.

        Provider-specific symbol conversion should be implemented in
        the concrete provider.

        Example:

            eur_usd -> EUR_USD
        """

        if not isinstance(
            symbol,
            str,
        ):
            raise TypeError(
                "symbol must be a string."
            )

        normalized = (
            symbol
            .strip()
            .upper()
        )

        if not normalized:
            raise ValueError(
                "symbol cannot be empty."
            )

        return normalized

    # ------------------------------------------------------------------
    # Candle validation
    # ------------------------------------------------------------------

    @classmethod
    def validate_candles(
        cls,
        candles: Iterable[Candle],
        *,
        expected_symbol: str | None = None,
        require_sorted: bool = True,
        reject_duplicates: bool = True,
    ) -> list[Candle]:
        """
        Validate and normalize a collection of Candle objects.

        This is the final safety boundary between external market-data
        providers and the analysis engine.

        Guarantees:

        - every item is a Candle
        - timestamps are timezone-aware
        - symbols are not empty
        - optional symbol consistency is enforced
        - duplicate timestamps can be rejected
        - chronological ordering can be enforced
        - returned collection is a new list
        """

        if candles is None:
            raise ValueError(
                "candles cannot be None."
            )

        result = list(candles)

        if not result:
            return []

        for index, candle in enumerate(
            result
        ):
            if not isinstance(
                candle,
                Candle,
            ):
                raise TypeError(
                    "All candle values must be "
                    f"Candle instances. Invalid item "
                    f"at index {index}."
                )

            if candle.timestamp.tzinfo is None:
                raise ValueError(
                    "Candle timestamp must be "
                    "timezone-aware."
                )

            if not candle.symbol.strip():
                raise ValueError(
                    "Candle symbol cannot be empty."
                )

        # --------------------------------------------------------------
        # Expected symbol validation
        # --------------------------------------------------------------

        if expected_symbol is not None:
            normalized_symbol = cls.normalize_symbol(
                expected_symbol
            )

            for candle in result:
                if (
                    cls.normalize_symbol(
                        candle.symbol
                    )
                    != normalized_symbol
                ):
                    raise ValueError(
                        "Candle symbol does not match "
                        f"requested symbol "
                        f"{expected_symbol!r}."
                    )

        # --------------------------------------------------------------
        # Duplicate timestamp detection
        # --------------------------------------------------------------

        if reject_duplicates:
            seen: set[tuple[str, datetime]] = set()

            for candle in result:
                key = (
                    cls.normalize_symbol(
                        candle.symbol
                    ),
                    candle.timestamp,
                )

                if key in seen:
                    raise ValueError(
                        "Duplicate candle detected for "
                        f"{candle.symbol} at "
                        f"{candle.timestamp.isoformat()}."
                    )

                seen.add(key)

        # --------------------------------------------------------------
        # Chronological validation
        # --------------------------------------------------------------

        if require_sorted:
            for previous, current in zip(
                result,
                result[1:],
            ):
                if current.timestamp <= previous.timestamp:
                    raise ValueError(
                        "Candles must be strictly ordered "
                        "chronologically."
                    )

        return result

    # ------------------------------------------------------------------
    # Candle sorting / deduplication
    # ------------------------------------------------------------------

    @classmethod
    def normalize_candles(
        cls,
        candles: Iterable[Candle],
        *,
        expected_symbol: str | None = None,
        deduplicate: bool = True,
    ) -> list[Candle]:
        """
        Normalize an arbitrary provider result into a deterministic
        chronological candle sequence.

        Unlike validate_candles(), this method is intentionally tolerant
        of provider ordering.

        It:

        1. validates Candle objects
        2. optionally validates the requested symbol
        3. sorts by timestamp
        4. optionally removes duplicate timestamps

        If duplicates exist, the last occurrence is retained.
        """

        if candles is None:
            raise ValueError(
                "candles cannot be None."
            )

        items = list(candles)

        for index, candle in enumerate(
            items
        ):
            if not isinstance(
                candle,
                Candle,
            ):
                raise TypeError(
                    "All candle values must be "
                    f"Candle instances. Invalid item "
                    f"at index {index}."
                )

        if expected_symbol is not None:
            normalized_symbol = cls.normalize_symbol(
                expected_symbol
            )

            for candle in items:
                if (
                    cls.normalize_symbol(
                        candle.symbol
                    )
                    != normalized_symbol
                ):
                    raise ValueError(
                        "Candle symbol does not match "
                        f"requested symbol "
                        f"{expected_symbol!r}."
                    )

        if not deduplicate:
            return sorted(
                items,
                key=lambda candle: candle.timestamp,
            )

        unique: dict[
            tuple[str, datetime],
            Candle,
        ] = {}

        for candle in items:
            key = (
                cls.normalize_symbol(
                    candle.symbol
                ),
                candle.timestamp,
            )

            unique[key] = candle

        return sorted(
            unique.values(),
            key=lambda candle: candle.timestamp,
        )

    # ------------------------------------------------------------------
    # Limit helper
    # ------------------------------------------------------------------

    @classmethod
    def apply_limit(
        cls,
        candles: Iterable[Candle],
        limit: int,
    ) -> list[Candle]:
        """
        Apply the requested candle limit while preserving the newest
        candles.

        Example:

            500 candles + limit=100
            -> newest 100 candles
        """

        if isinstance(
            limit,
            bool,
        ):
            raise TypeError(
                "limit must be an integer."
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

        if limit > cls.MAX_LIMIT:
            raise ValueError(
                f"limit cannot exceed "
                f"{cls.MAX_LIMIT}."
            )

        items = list(candles)

        if len(items) <= limit:
            return items

        return items[-limit:]

    # ------------------------------------------------------------------
    # Timeframe helper
    # ------------------------------------------------------------------

    @staticmethod
    def normalize_timeframe(
        timeframe: str,
    ) -> str:
        """
        Normalize common project timeframe notation.

        This method intentionally does not decide whether a provider
        supports a timeframe. Concrete providers remain responsible
        for provider-specific support.

        Examples:

            M1  -> M1
            M5  -> M5
            M15 -> M15
            H1  -> H1
            D1  -> D1
        """

        if not isinstance(
            timeframe,
            str,
        ):
            raise TypeError(
                "timeframe must be a string."
            )

        normalized = (
            timeframe
            .strip()
            .upper()
        )

        if not normalized:
            raise ValueError(
                "timeframe cannot be empty."
            )

        aliases: dict[str, str] = {
            "1M": "M1",
            "5M": "M5",
            "15M": "M15",
            "30M": "M30",
            "60M": "H1",
            "1H": "H1",
            "1HR": "H1",
            "1D": "D1",
            "1DAY": "D1",
            "1W": "W1",
            "1WEEK": "W1",
        }

        return aliases.get(
            normalized,
            normalized,
        )

    # ------------------------------------------------------------------
    # Provider representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        """
        Provide a useful provider representation for logs/debugging.
        """

        provider_name = getattr(
            self,
            "name",
            self.__class__.__name__,
        )

        return (
            f"{self.__class__.__name__}"
            f"(name={provider_name!r})"
        )


__all__ = [
    "MarketDataProvider",
]

