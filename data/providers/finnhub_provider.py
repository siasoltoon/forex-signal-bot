from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
from typing import Final

from core.errors import ApplicationError
from core.logger import setup_logger

from data.base import MarketDataProvider
from data.models import Candle
from data.providers.clients.finnhub import FinnhubClient


logger = setup_logger()


class FinnhubProvider(MarketDataProvider):
    """
    Production-grade Finnhub market-data provider.

    Responsibilities
    ----------------
    - Validate and normalize requests.
    - Convert project timeframes to Finnhub resolutions.
    - Calculate safe UTC time ranges.
    - Fetch candle data through FinnhubClient.
    - Validate the returned payload.
    - Reject malformed / impossible candles.
    - Remove duplicate timestamps.
    - Sort candles chronologically.
    - Enforce the requested candle limit.
    - Return provider-independent Candle objects.

    Backward compatibility
    ----------------------
    The existing public API is intentionally preserved:

        FinnhubProvider()
        provider.name
        await provider.get_candles(...)

    No existing file/class names are changed.
    """

    # ------------------------------------------------------------------
    # Provider metadata
    # ------------------------------------------------------------------

    name = "finnhub"

    # Finnhub supports these resolutions for candle requests.
    _TIMEFRAME_ALIASES: Final[dict[str, str]] = {
        # Minutes
        "1M": "1",
        "1MIN": "1",
        "1MINUTE": "1",

        "5M": "5",
        "5MIN": "5",
        "5MINUTE": "5",

        "15M": "15",
        "15MIN": "15",
        "15MINUTE": "15",

        "30M": "30",
        "30MIN": "30",
        "30MINUTE": "30",

        # Hours
        "1H": "60",
        "1HR": "60",
        "1HOUR": "60",
        "H1": "60",

        # Daily / weekly / monthly
        "D": "D",
        "1D": "D",
        "1DAY": "D",

        "W": "W",
        "1W": "W",
        "1WEEK": "W",

        "M": "M",
        "1MO": "M",
        "1MONTH": "M",
    }

    _TIMEFRAME_MINUTES: Final[dict[str, int]] = {
        "1": 1,
        "5": 5,
        "15": 15,
        "30": 30,
        "60": 60,
        "D": 1440,
        "W": 10080,
        "M": 43200,
    }

    # Finnhub's candle endpoint has provider-specific limits.
    # Keep the generic project's maximum as the hard ceiling.
    MAX_LIMIT: Final[int] = 5000

    # Small safety margin used when calculating historical ranges.
    _RANGE_MARGIN_CANDLES: Final[int] = 1

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(
        self,
        client: FinnhubClient | None = None,
    ) -> None:
        """
        Create the provider.

        Dependency injection is supported so tests and future services
        can provide a custom FinnhubClient implementation.
        """

        self.client = (
            client
            if client is not None
            else FinnhubClient()
        )

    # ------------------------------------------------------------------
    # Provider status
    # ------------------------------------------------------------------

    def is_configured(self) -> bool:
        """
        Return whether the underlying Finnhub client has credentials.

        We intentionally avoid making a network request here.
        """

        api_key = getattr(
            self.client,
            "api_key",
            None,
        )

        return bool(
            isinstance(api_key, str)
            and api_key.strip()
        )

    async def health_check(self) -> bool:
        """
        Lightweight provider health check.

        Configuration is checked locally. A network request is not
        performed because this method should remain safe and cheap.
        """

        return self.is_configured()

    # ------------------------------------------------------------------
    # Timeframe handling
    # ------------------------------------------------------------------

    @classmethod
    def _normalize_timeframe(
        cls,
        timeframe: str,
    ) -> str:
        """
        Convert project timeframe notation to Finnhub resolution.

        Examples
        --------
        M15 -> 15
        15m -> 15
        H1  -> 60
        1h  -> 60
        D   -> D
        1d  -> D
        W   -> W
        M   -> M

        Important:
            Finnhub uses "M" for month while the project commonly uses
            "M15" for 15 minutes. The explicit aliases above prevent
            ambiguity.
        """

        if not isinstance(
            timeframe,
            str,
        ):
            raise TypeError(
                "timeframe must be a string."
            )

        normalized = timeframe.strip()

        if not normalized:
            raise ValueError(
                "timeframe cannot be empty."
            )

        # Exact aliases first.
        alias = cls._TIMEFRAME_ALIASES.get(
            normalized.upper()
        )

        if alias is not None:
            return alias

        # Generic minute formats.
        compact = normalized.lower()

        minute_aliases = {
            "1m": "1",
            "5m": "5",
            "15m": "15",
            "30m": "30",
        }

        if compact in minute_aliases:
            return minute_aliases[compact]

        # Generic hour format.
        if compact in {
            "1h",
            "1hr",
            "1hour",
        }:
            return "60"

        # Generic day / week formats.
        if compact in {
            "1d",
            "1day",
        }:
            return "D"

        if compact in {
            "1w",
            "1week",
        }:
            return "W"

        # Month must remain uppercase.
        if normalized in {
            "M",
            "1MO",
            "1MONTH",
        }:
            return "M"

        return normalized.upper()

    @classmethod
    def _validate_timeframe(
        cls,
        timeframe: str,
    ) -> str:
        """
        Normalize and validate a Finnhub timeframe.
        """

        normalized = cls._normalize_timeframe(
            timeframe
        )

        if normalized not in cls._TIMEFRAME_MINUTES:
            raise ValueError(
                "Unsupported Finnhub timeframe: "
                f"{timeframe!r}"
            )

        return normalized

    # ------------------------------------------------------------------
    # Request validation
    # ------------------------------------------------------------------

    @classmethod
    def _validate_request(
        cls,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> tuple[str, str, int]:
        """
        Validate and normalize the complete request.

        We preserve ValueError / TypeError behavior expected by the
        existing project tests while using the common provider contract
        wherever possible.
        """

        if not isinstance(
            symbol,
            str,
        ):
            raise TypeError(
                "symbol must be a string."
            )

        normalized_symbol = symbol.strip().upper()

        if not normalized_symbol:
            raise ValueError(
                "symbol cannot be empty."
            )

        if len(normalized_symbol) > 30:
            raise ValueError(
                "symbol is too long."
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

        resolution = cls._validate_timeframe(
            timeframe
        )

        return (
            normalized_symbol,
            resolution,
            limit,
        )

    # ------------------------------------------------------------------
    # Time range
    # ------------------------------------------------------------------

    @classmethod
    def _calculate_time_range(
        cls,
        timeframe: str,
        limit: int,
    ) -> tuple[int, int]:
        """
        Calculate a UTC Unix timestamp range.

        One extra candle is requested from the provider to reduce the
        chance of returning fewer candles because of boundary rounding.
        """

        resolution = cls._validate_timeframe(
            timeframe
        )

        minutes = cls._TIMEFRAME_MINUTES[
            resolution
        ]

        now = datetime.now(
            timezone.utc
        )

        end_timestamp = int(
            now.timestamp()
        )

        effective_limit = (
            limit
            + cls._RANGE_MARGIN_CANDLES
        )

        total_seconds = (
            minutes
            * 60
            * effective_limit
        )

        start_timestamp = (
            end_timestamp
            - total_seconds
        )

        return (
            start_timestamp,
            end_timestamp,
        )

    # ------------------------------------------------------------------
    # Primitive parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_timestamp(
        value: object,
    ) -> datetime:
        """
        Convert a Finnhub Unix timestamp to UTC datetime.
        """

        try:
            timestamp = int(
                float(value)
            )
        except (
            TypeError,
            ValueError,
            OverflowError,
        ) as error:
            raise ValueError(
                "Invalid Finnhub timestamp."
            ) from error

        if timestamp <= 0:
            raise ValueError(
                "Finnhub timestamp must be positive."
            )

        return datetime.fromtimestamp(
            timestamp,
            tz=timezone.utc,
        )

    @staticmethod
    def _parse_price(
        value: object,
    ) -> float:
        """
        Convert and validate a price.
        """

        try:
            price = float(value)
        except (
            TypeError,
            ValueError,
            OverflowError,
        ) as error:
            raise ValueError(
                "Invalid price value."
            ) from error

        if not isfinite(price):
            raise ValueError(
                "Price must be finite."
            )

        if price <= 0:
            raise ValueError(
                "Price must be greater than zero."
            )

        return price

    @staticmethod
    def _parse_volume(
        value: object,
    ) -> float:
        """
        Convert and validate volume.
        """

        try:
            volume = float(value)
        except (
            TypeError,
            ValueError,
            OverflowError,
        ) as error:
            raise ValueError(
                "Invalid volume value."
            ) from error

        if not isfinite(volume):
            raise ValueError(
                "Volume must be finite."
            )

        if volume < 0:
            raise ValueError(
                "Volume cannot be negative."
            )

        return volume

    # ------------------------------------------------------------------
    # Candle validation / conversion
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_ohlc(
        open_price: float,
        high: float,
        low: float,
        close: float,
    ) -> None:
        """
        Validate OHLC structural consistency.
        """

        if high < low:
            raise ValueError(
                "high cannot be lower than low."
            )

        if high < max(
            open_price,
            close,
        ):
            raise ValueError(
                "high must be >= open and close."
            )

        if low > min(
            open_price,
            close,
        ):
            raise ValueError(
                "low must be <= open and close."
            )

    def _convert_candle(
        self,
        symbol: str,
        timestamp: object,
        open_price: object,
        high: object,
        low: object,
        close: object,
        volume: object,
    ) -> Candle | None:
        """
        Convert one Finnhub candle into the project's Candle model.

        Invalid individual candles are skipped rather than destroying
        the entire valid response.
        """

        try:
            parsed_open = self._parse_price(
                open_price
            )

            parsed_high = self._parse_price(
                high
            )

            parsed_low = self._parse_price(
                low
            )

            parsed_close = self._parse_price(
                close
            )

            parsed_volume = self._parse_volume(
                volume
            )

            self._validate_ohlc(
                open_price=parsed_open,
                high=parsed_high,
                low=parsed_low,
                close=parsed_close,
            )

            return Candle(
                symbol=symbol,
                timestamp=self._parse_timestamp(
                    timestamp
                ),
                open=parsed_open,
                high=parsed_high,
                low=parsed_low,
                close=parsed_close,
                volume=parsed_volume,
            )

        except (
            TypeError,
            ValueError,
            OverflowError,
        ) as error:
            logger.warning(
                "Skipping invalid Finnhub candle "
                "for %s: %s",
                symbol,
                error,
            )

            return None

    # ------------------------------------------------------------------
    # Response validation
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_arrays(
        response: dict,
    ) -> tuple[
        list,
        list,
        list,
        list,
        list,
        list,
    ]:
        """
        Extract Finnhub OHLCV arrays and validate their structure.
        """

        timestamps = response.get(
            "t",
            []
        )

        opens = response.get(
            "o",
            []
        )

        highs = response.get(
            "h",
            []
        )

        lows = response.get(
            "l",
            []
        )

        closes = response.get(
            "c",
            []
        )

        volumes = response.get(
            "v",
            []
        )

        arrays = (
            timestamps,
            opens,
            highs,
            lows,
            closes,
            volumes,
        )

        if not all(
            isinstance(
                value,
                list,
            )
            for value in arrays
        ):
            raise ApplicationError(
                "Invalid Finnhub candle payload.",
                {
                    "provider": "finnhub",
                },
            )

        lengths = {
            len(timestamps),
            len(opens),
            len(highs),
            len(lows),
            len(closes),
            len(volumes),
        }

        if len(lengths) != 1:
            raise ApplicationError(
                "Finnhub candle arrays have "
                "inconsistent lengths.",
                {
                    "provider": "finnhub",
                },
            )

        return (
            timestamps,
            opens,
            highs,
            lows,
            closes,
            volumes,
        )

    # ------------------------------------------------------------------
    # Candle deduplication
    # ------------------------------------------------------------------

    @staticmethod
    def _deduplicate_candles(
        candles: list[Candle],
    ) -> list[Candle]:
        """
        Remove duplicate candles by timestamp.

        Finnhub data is normally unique, but this defensive layer keeps
        duplicate records from leaking into analysis and indicators.
        """

        unique: dict[datetime, Candle] = {}

        for candle in candles:
            unique[candle.timestamp] = candle

        return list(
            sorted(
                unique.values(),
                key=lambda candle: candle.timestamp,
            )
        )

    # ------------------------------------------------------------------
    # Main provider API
    # ------------------------------------------------------------------

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> list[Candle]:
        """
        Fetch and normalize Finnhub candle data.

        Returns
        -------
        list[Candle]
            Chronologically sorted, validated and deduplicated candles.

        Raises
        ------
        ValueError
            Invalid symbol, timeframe or limit.

        ApplicationError
            Network/provider/response errors.
        """

        (
            normalized_symbol,
            resolution,
            validated_limit,
        ) = self._validate_request(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

        (
            from_timestamp,
            to_timestamp,
        ) = self._calculate_time_range(
            timeframe=resolution,
            limit=validated_limit,
        )

        # --------------------------------------------------------------
        # Provider configuration
        # --------------------------------------------------------------

        if not self.is_configured():
            logger.warning(
                "Finnhub provider is not configured."
            )

        # --------------------------------------------------------------
        # API request
        # --------------------------------------------------------------

        try:
            response = (
                await self.client.get_candles(
                    symbol=normalized_symbol,
                    resolution=resolution,
                    from_timestamp=from_timestamp,
                    to_timestamp=to_timestamp,
                )
            )

        except Exception as error:
            logger.exception(
                "Finnhub candle request failed "
                "for %s [%s].",
                normalized_symbol,
                resolution,
            )

            raise ApplicationError(
                "Failed to fetch Finnhub candles.",
                {
                    "provider": self.name,
                    "symbol": normalized_symbol,
                    "timeframe": resolution,
                    "limit": validated_limit,
                },
            ) from error

        # --------------------------------------------------------------
        # Empty response
        # --------------------------------------------------------------

        if response is None:
            logger.warning(
                "Finnhub returned no candle data "
                "for %s.",
                normalized_symbol,
            )

            return []

        # --------------------------------------------------------------
        # Response type
        # --------------------------------------------------------------

        if not isinstance(
            response,
            dict,
        ):
            raise ApplicationError(
                "Invalid Finnhub response.",
                {
                    "provider": self.name,
                    "symbol": normalized_symbol,
                },
            )

        # --------------------------------------------------------------
        # Finnhub status
        # --------------------------------------------------------------

        status = response.get("s")

        if status != "ok":
            logger.warning(
                "Finnhub returned non-ok status "
                "for %s: %s",
                normalized_symbol,
                status,
            )

            return []

        # --------------------------------------------------------------
        # Extract and validate payload
        # --------------------------------------------------------------

        try:
            (
                timestamps,
                opens,
                highs,
                lows,
                closes,
                volumes,
            ) = self._extract_arrays(
                response
            )

        except ApplicationError:
            raise

        except Exception as error:
            logger.exception(
                "Failed to parse Finnhub response "
                "for %s.",
                normalized_symbol,
            )

            raise ApplicationError(
                "Failed to parse Finnhub candle response.",
                {
                    "provider": self.name,
                    "symbol": normalized_symbol,
                },
            ) from error

        # --------------------------------------------------------------
        # Convert candles
        # --------------------------------------------------------------

        candles: list[Candle] = []

        for (
            timestamp,
            open_price,
            high,
            low,
            close,
            volume,
        ) in zip(
            timestamps,
            opens,
            highs,
            lows,
            closes,
            volumes,
        ):
            candle = self._convert_candle(
                symbol=normalized_symbol,
                timestamp=timestamp,
                open_price=open_price,
                high=high,
                low=low,
                close=close,
                volume=volume,
            )

            if candle is not None:
                candles.append(
                    candle
                )

        # --------------------------------------------------------------
        # Sort + deduplicate
        # --------------------------------------------------------------

        candles = self._deduplicate_candles(
            candles
        )

        # --------------------------------------------------------------
        # Enforce requested limit
        # --------------------------------------------------------------

        if len(candles) > validated_limit:
            candles = candles[
                -validated_limit:
            ]

        # --------------------------------------------------------------
        # Final provider-independent validation
        # --------------------------------------------------------------

        try:
            candles = self.validate_candles(
                candles
            )

        except Exception as error:
            logger.exception(
                "Finnhub produced invalid "
                "standardized candles for %s.",
                normalized_symbol,
            )

            raise ApplicationError(
                "Finnhub returned invalid market data.",
                {
                    "provider": self.name,
                    "symbol": normalized_symbol,
                    "timeframe": resolution,
                },
            ) from error

        logger.info(
            "Finnhub returned %d valid candles "
            "for %s [%s].",
            len(candles),
            normalized_symbol,
            resolution,
        )

        return candles


__all__ = [
    "FinnhubProvider",
]
