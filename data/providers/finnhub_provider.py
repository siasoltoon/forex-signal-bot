
from __future__ import annotations

from datetime import datetime, timezone
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
    - Validate incoming market-data requests.
    - Normalize symbols and timeframes.
    - Translate the project's timeframe contract to Finnhub
      resolution values.
    - Calculate a safe historical time range.
    - Fetch candles through FinnhubClient.
    - Validate and normalize Finnhub responses.
    - Convert provider payloads into provider-independent Candle objects.
    - Preserve the existing project's public API.

    Backward compatibility
    ----------------------
    Existing project code can continue using:

        provider.name
        provider.get_candles(...)
        FinnhubProvider()

    Supported project timeframe aliases include:

        M1 / 1m
        M5 / 5m
        M15 / 15m
        M30 / 30m
        H1 / 1h
        D / 1d
        W / 1w
        M / 1M
    """

    # ------------------------------------------------------------------
    # Provider metadata
    # ------------------------------------------------------------------

    name = "finnhub"

    # Finnhub resolution values.
    #
    # The project's external timeframe contract is intentionally broader
    # and more human-friendly. These aliases translate that contract into
    # the exact resolution values expected by Finnhub.
    _TIMEFRAME_ALIASES: Final[dict[str, str]] = {
        # Minutes
        "M1": "1",
        "1M": "1",
        "1MIN": "1",
        "1MINUTE": "1",

        "M5": "5",
        "5M": "5",
        "5MIN": "5",
        "5MINUTE": "5",

        "M15": "15",
        "15M": "15",
        "15MIN": "15",
        "15MINUTE": "15",

        "M30": "30",
        "30M": "30",
        "30MIN": "30",
        "30MINUTE": "30",

        # Hour
        "H1": "60",
        "1H": "60",
        "1HR": "60",
        "1HOUR": "60",

        # Daily
        "D": "D",
        "1D": "D",
        "1DAY": "D",
        "DAILY": "D",

        # Weekly
        "W": "W",
        "1W": "W",
        "1WEEK": "W",
        "WEEKLY": "W",

        # Monthly
        #
        # Important:
        # "M" is treated as month in this provider's public alias table,
        # while minute values use M1/M5/M15/M30.
        "M": "M",
        "1MONTH": "M",
        "MONTHLY": "M",
    }

    # Resolution -> approximate duration in minutes.
    #
    # This is used only for calculating the historical request window.
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

    # Finnhub's API and the generic provider contract should never be
    # allowed to receive an unbounded candle request.
    _MAX_LIMIT: Final[int] = 5000

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(
        self,
        client: FinnhubClient | None = None,
    ) -> None:
        """
        Create the Finnhub provider.

        A client can be injected for:
        - unit tests
        - integration tests
        - dependency injection
        - future client pooling
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
        Return whether the underlying Finnhub client is configured.

        The client is intentionally queried defensively so that this
        provider remains compatible with the current client implementation
        and future versions.
        """

        checker = getattr(
            self.client,
            "is_configured",
            None,
        )

        if callable(checker):
            try:
                return bool(checker())
            except Exception:
                logger.exception(
                    "Finnhub configuration check failed."
                )
                return False

        # Existing client implementations may not expose is_configured.
        # In that case construction itself is considered sufficient.
        return True

    # ------------------------------------------------------------------
    # Timeframe normalization
    # ------------------------------------------------------------------

    @classmethod
    def _normalize_timeframe(
        cls,
        timeframe: str,
    ) -> str:
        """
        Normalize a project timeframe into a Finnhub resolution.

        Examples
        --------
        M15  -> 15
        15m  -> 15
        H1   -> 60
        1h   -> 60
        D    -> D
        1d   -> D
        W    -> W
        1w   -> W
        M    -> M
        1M   -> 1

        Note
        ----
        The uppercase conversion is deliberately followed by explicit
        alias handling because "M" has historically been used by this
        project as the monthly timeframe while minute values use M1/M5/
        M15/M30.
        """

        if not isinstance(
            timeframe,
            str,
        ):
            raise TypeError(
                "timeframe must be a string."
            )

        raw = timeframe.strip()

        if not raw:
            raise ValueError(
                "timeframe cannot be empty."
            )

        # Preserve the distinction between:
        #   1m  -> minute
        #   1M  -> monthly
        #
        # Before uppercasing, handle common lowercase minute notation.
        compact = raw.replace(
            " ",
            "",
        )

        lower = compact.lower()

        lowercase_minute_aliases: dict[str, str] = {
            "1m": "1",
            "5m": "5",
            "15m": "15",
            "30m": "30",
            "1min": "1",
            "5min": "5",
            "15min": "15",
            "30min": "30",
            "1minute": "1",
            "5minute": "5",
            "15minute": "15",
            "30minute": "30",
        }

        if lower in lowercase_minute_aliases:
            return lowercase_minute_aliases[lower]

        normalized = compact.upper()

        return cls._TIMEFRAME_ALIASES.get(
            normalized,
            normalized,
        )

    @classmethod
    def _validate_timeframe(
        cls,
        timeframe: str,
    ) -> str:
        """
        Normalize and validate a Finnhub timeframe.

        Returns
        -------
        str
            Exact Finnhub resolution value.
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
    ) -> None:
        """
        Validate a candle request before contacting Finnhub.
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

        if limit > cls._MAX_LIMIT:
            raise ValueError(
                f"limit cannot exceed "
                f"{cls._MAX_LIMIT}."
            )

        # Validate the actual provider resolution as well.
        cls._validate_timeframe(
            timeframe
        )

    # ------------------------------------------------------------------
    # Historical range
    # ------------------------------------------------------------------

    @classmethod
    def _calculate_time_range(
        cls,
        timeframe: str,
        limit: int,
    ) -> tuple[int, int]:
        """
        Calculate the Unix timestamp range needed for a candle request.

        The returned values are UTC timestamps.
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

        total_seconds = (
            minutes
            * 60
            * limit
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
    # Symbol normalization
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_symbol(
        symbol: str,
    ) -> str:
        """
        Normalize a project symbol for Finnhub.

        EUR_USD becomes EUR_USD.

        The provider client remains responsible for any additional
        provider-specific symbol transformation required by Finnhub.
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
    # Timestamp parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_timestamp(
        value: object,
    ) -> datetime:
        """
        Convert a Finnhub Unix timestamp into UTC datetime.
        """

        try:
            timestamp = int(value)
        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                "Finnhub timestamp must be an integer."
            ) from error

        if timestamp <= 0:
            raise ValueError(
                "Finnhub timestamp must be positive."
            )

        return datetime.fromtimestamp(
            timestamp,
            tz=timezone.utc,
        )

    # ------------------------------------------------------------------
    # Numeric parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_price(
        value: object,
    ) -> float:
        """
        Parse and validate an OHLC price.
        """

        try:
            price = float(value)
        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                "Finnhub price must be numeric."
            ) from error

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
        Parse and validate candle volume.
        """

        try:
            volume = float(value)
        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                "Finnhub volume must be numeric."
            ) from error

        if volume < 0:
            raise ValueError(
                "Volume cannot be negative."
            )

        return volume

    # ------------------------------------------------------------------
    # Candle conversion
    # ------------------------------------------------------------------

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
        Convert one Finnhub OHLCV record into a Candle.

        Invalid individual candles are skipped rather than causing an
        otherwise valid response to fail completely.
        """

        try:
            candle = Candle(
                symbol=symbol,
                timestamp=self._parse_timestamp(
                    timestamp
                ),
                open=self._parse_price(
                    open_price
                ),
                high=self._parse_price(
                    high
                ),
                low=self._parse_price(
                    low
                ),
                close=self._parse_price(
                    close
                ),
                volume=self._parse_volume(
                    volume
                ),
            )

            return candle

        except (
            TypeError,
            ValueError,
            OverflowError,
        ) as error:
            logger.warning(
                "Skipping invalid Finnhub candle: %s",
                error,
            )

            return None

    # ------------------------------------------------------------------
    # Response validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_response_structure(
        response: object,
        symbol: str,
    ) -> dict:
        """
        Validate the basic Finnhub response structure.
        """

        if response is None:
            return {}

        if not isinstance(
            response,
            dict,
        ):
            raise ApplicationError(
                "Invalid Finnhub response.",
                {
                    "provider": "finnhub",
                    "symbol": symbol,
                },
            )

        return response

    @staticmethod
    def _extract_arrays(
        response: dict,
        symbol: str,
    ) -> tuple[
        list,
        list,
        list,
        list,
        list,
        list,
    ]:
        """
        Extract and validate the six Finnhub candle arrays.
        """

        timestamps = response.get(
            "t",
            [],
        )

        opens = response.get(
            "o",
            [],
        )

        highs = response.get(
            "h",
            [],
        )

        lows = response.get(
            "l",
            [],
        )

        closes = response.get(
            "c",
            [],
        )

        volumes = response.get(
            "v",
            [],
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
                    "symbol": symbol,
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
                    "symbol": symbol,
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
    # Main market-data API
    # ------------------------------------------------------------------

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> list[Candle]:
        """
        Fetch and normalize Finnhub candles.

        Parameters
        ----------
        symbol:
            Market symbol, e.g. EUR_USD.

        timeframe:
            Project timeframe such as M15, 15m, H1, 1h, D or 1d.

        limit:
            Maximum number of candles to return.

        Returns
        -------
        list[Candle]
            Provider-independent candle objects.
        """

        # --------------------------------------------------------------
        # Validate request
        # --------------------------------------------------------------

        self._validate_request(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

        normalized_symbol = (
            self._normalize_symbol(
                symbol
            )
        )

        resolution = (
            self._validate_timeframe(
                timeframe
            )
        )

        (
            from_timestamp,
            to_timestamp,
        ) = self._calculate_time_range(
            timeframe=resolution,
            limit=limit,
        )

        # --------------------------------------------------------------
        # Request Finnhub
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
                "for %s.",
                normalized_symbol,
            )

            raise ApplicationError(
                "Failed to fetch Finnhub candles.",
                {
                    "provider": self.name,
                    "symbol": normalized_symbol,
                    "timeframe": resolution,
                    "limit": limit,
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
        # Validate response object
        # --------------------------------------------------------------

        response = self._validate_response_structure(
            response=response,
            symbol=normalized_symbol,
        )

        if not response:
            return []

        # --------------------------------------------------------------
        # Finnhub status
        # --------------------------------------------------------------

        status = response.get(
            "s"
        )

        if status != "ok":
            logger.warning(
                "Finnhub returned non-ok status "
                "for %s: %s",
                normalized_symbol,
                status,
            )

            return []

        # --------------------------------------------------------------
        # Extract OHLCV arrays
        # --------------------------------------------------------------

        (
            timestamps,
            opens,
            highs,
            lows,
            closes,
            volumes,
        ) = self._extract_arrays(
            response=response,
            symbol=normalized_symbol,
        )

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
        # Sort chronologically
        # --------------------------------------------------------------

        candles.sort(
            key=lambda candle: candle.timestamp
        )

        # --------------------------------------------------------------
        # Enforce requested limit
        # --------------------------------------------------------------

        if len(candles) > limit:
            candles = candles[
                -limit:
            ]

        # --------------------------------------------------------------
        # Validate final provider-independent result
        # --------------------------------------------------------------

        try:
            candles = self.validate_candles(
                candles
            )
        except Exception as error:
            logger.exception(
                "Finnhub produced an invalid "
                "standardized candle result."
            )

            raise ApplicationError(
                "Finnhub returned invalid standardized candles.",
                {
                    "provider": self.name,
                    "symbol": normalized_symbol,
                    "timeframe": resolution,
                },
            ) from error

        logger.info(
            "Finnhub returned %d valid candles "
            "for %s (%s).",
            len(candles),
            normalized_symbol,
            resolution,
        )

        return candles


__all__ = [
    "FinnhubProvider",
]

