
from __future__ import annotations

from datetime import datetime, timezone
from typing import Final

from core.errors import ApplicationError
from core.logger import setup_logger

from data.base import MarketDataProvider
from data.models import Candle
from data.providers.clients.alphavantage import AlphaVantageClient


logger = setup_logger()


class AlphaVantageProvider(MarketDataProvider):
    """
    Production-grade Alpha Vantage market-data provider.

    This class translates the project's common market-data contract
    into Alpha Vantage's intraday API format.

    Backward-compatible public API:

        AlphaVantageProvider()
        provider.name
        provider.get_candles(...)

    Supported project timeframe formats include:

        M1 / 1m
        M5 / 5m
        M15 / 15m
        M30 / 30m
        H1 / 1h
    """

    # ------------------------------------------------------------------
    # Provider metadata
    # ------------------------------------------------------------------

    name = "alphavantage"

    # Alpha Vantage intraday API intervals.
    _TIMEFRAME_ALIASES: Final[dict[str, str]] = {
        # 1 minute
        "M1": "1min",
        "1M": "1min",
        "1MIN": "1min",
        "1MINUTE": "1min",

        # 5 minutes
        "M5": "5min",
        "5M": "5min",
        "5MIN": "5min",
        "5MINUTE": "5min",

        # 15 minutes
        "M15": "15min",
        "15M": "15min",
        "15MIN": "15min",
        "15MINUTE": "15min",

        # 30 minutes
        "M30": "30min",
        "30M": "30min",
        "30MIN": "30min",
        "30MINUTE": "30min",

        # 1 hour
        "H1": "60min",
        "1H": "60min",
        "1HR": "60min",
        "1HOUR": "60min",
    }

    _SUPPORTED_INTERVALS: Final[frozenset[str]] = frozenset(
        {
            "1min",
            "5min",
            "15min",
            "30min",
            "60min",
        }
    )

    _INTERVAL_MINUTES: Final[dict[str, int]] = {
        "1min": 1,
        "5min": 5,
        "15min": 15,
        "30min": 30,
        "60min": 60,
    }

    _MAX_LIMIT: Final[int] = 5000

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(
        self,
        client: AlphaVantageClient | None = None,
    ) -> None:
        """
        Create the provider.

        Dependency injection is supported so unit tests can replace
        the real API client without making network requests.
        """

        self.client = (
            client
            if client is not None
            else AlphaVantageClient()
        )

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def is_configured(self) -> bool:
        """
        Return whether the underlying client has an API key configured.
        """

        api_key = getattr(
            self.client,
            "api_key",
            None,
        )

        return bool(
            api_key
            and str(api_key).strip()
        )

    # ------------------------------------------------------------------
    # Timeframe normalization
    # ------------------------------------------------------------------

    @classmethod
    def _normalize_timeframe(
        cls,
        timeframe: str,
    ) -> str:
        """
        Normalize a project timeframe into Alpha Vantage's interval.

        Examples:

            M15  -> 15min
            15m  -> 15min
            M30  -> 30min
            30m  -> 30min
            H1   -> 60min
            1h   -> 60min
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

        compact = raw.replace(
            " ",
            "",
        )

        # Lowercase minute notation must be handled before uppercase
        # normalization because "1m" means one minute in the common
        # project notation.
        lowercase_aliases: dict[str, str] = {
            "1m": "1min",
            "5m": "5min",
            "15m": "15min",
            "30m": "30min",
            "1min": "1min",
            "5min": "5min",
            "15min": "15min",
            "30min": "30min",
            "1minute": "1min",
            "5minute": "5min",
            "15minute": "15min",
            "30minute": "30min",
        }

        lower = compact.lower()

        if lower in lowercase_aliases:
            return lowercase_aliases[lower]

        normalized = compact.upper()

        interval = cls._TIMEFRAME_ALIASES.get(
            normalized
        )

        if interval is None:
            raise ValueError(
                "Unsupported Alpha Vantage timeframe: "
                f"{timeframe!r}"
            )

        return interval

    @classmethod
    def _validate_timeframe(
        cls,
        timeframe: str,
    ) -> str:
        """
        Normalize and validate a timeframe.
        """

        interval = cls._normalize_timeframe(
            timeframe
        )

        if interval not in cls._SUPPORTED_INTERVALS:
            raise ValueError(
                "Unsupported Alpha Vantage interval: "
                f"{interval!r}"
            )

        return interval

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
        Validate the common market-data request contract.
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

        cls._validate_timeframe(
            timeframe
        )

    # ------------------------------------------------------------------
    # Symbol normalization
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_symbol(
        symbol: str,
    ) -> str:
        """
        Normalize a project symbol.

        The provider-independent representation remains unchanged.

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
    # Timestamp parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_timestamp(
        value: object,
    ) -> datetime:
        """
        Parse Alpha Vantage's timestamp format.

        Alpha Vantage intraday timestamps are normally:

            YYYY-MM-DD HH:MM:SS
        """

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                "Alpha Vantage timestamp must be a string."
            )

        text = value.strip()

        if not text:
            raise ValueError(
                "Alpha Vantage timestamp cannot be empty."
            )

        formats = (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
        )

        for timestamp_format in formats:
            try:
                timestamp = datetime.strptime(
                    text,
                    timestamp_format,
                )

                return timestamp.replace(
                    tzinfo=timezone.utc
                )

            except ValueError:
                continue

        raise ValueError(
            "Unsupported Alpha Vantage timestamp format: "
            f"{value!r}"
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
                "Price must be numeric."
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
        Parse volume.

        Forex-style responses may not provide meaningful volume, so
        missing volume is normalized to zero.
        """

        if value is None:
            return 0.0

        try:
            volume = float(value)
        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                "Volume must be numeric."
            ) from error

        if volume < 0:
            raise ValueError(
                "Volume cannot be negative."
            )

        return volume

    # ------------------------------------------------------------------
    # Response helpers
    # ------------------------------------------------------------------

    @classmethod
    def _find_time_series(
        cls,
        response: dict[str, object],
    ) -> dict[str, object]:
        """
        Locate Alpha Vantage's time-series object.

        Alpha Vantage may return keys such as:

            Time Series (1min)
            Time Series (5min)
            Time Series (15min)
            Time Series (30min)
            Time Series (60min)
        """

        for key, value in response.items():
            if (
                isinstance(
                    key,
                    str,
                )
                and key.lower().startswith(
                    "time series"
                )
                and isinstance(
                    value,
                    dict,
                )
            ):
                return value

        raise ApplicationError(
            "Alpha Vantage time series was not found.",
            {
                "provider": cls.name,
            },
        )

    @staticmethod
    def _is_api_error_response(
        response: dict[str, object],
    ) -> bool:
        """
        Detect common Alpha Vantage error/rate-limit responses.
        """

        return any(
            key in response
            for key in (
                "Error Message",
                "Information",
                "Note",
            )
        )

    # ------------------------------------------------------------------
    # Candle conversion
    # ------------------------------------------------------------------

    def _convert_candle(
        self,
        symbol: str,
        timestamp_text: object,
        values: object,
    ) -> Candle | None:
        """
        Convert one Alpha Vantage record into a Candle.

        Invalid individual candles are skipped instead of invalidating
        the complete response.
        """

        if not isinstance(
            values,
            dict,
        ):
            logger.warning(
                "Skipping invalid Alpha Vantage candle payload."
            )
            return None

        try:
            return Candle(
                symbol=symbol,
                timestamp=self._parse_timestamp(
                    timestamp_text
                ),
                open=self._parse_price(
                    values["1. open"]
                ),
                high=self._parse_price(
                    values["2. high"]
                ),
                low=self._parse_price(
                    values["3. low"]
                ),
                close=self._parse_price(
                    values["4. close"]
                ),
                volume=self._parse_volume(
                    values.get(
                        "5. volume",
                        0,
                    )
                ),
            )

        except (
            KeyError,
            TypeError,
            ValueError,
            OverflowError,
        ) as error:
            logger.warning(
                "Skipping invalid Alpha Vantage candle: %s",
                error,
            )

            return None

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
        Fetch Alpha Vantage candles and convert them into the project's
        standard Candle model.
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

        interval = (
            self._validate_timeframe(
                timeframe
            )
        )

        # --------------------------------------------------------------
        # Fetch provider data
        # --------------------------------------------------------------

        try:
            response = (
                await self.client.get_intraday(
                    symbol=normalized_symbol,
                    interval=interval,
                )
            )

        except Exception as error:
            logger.exception(
                "Alpha Vantage candle request failed "
                "for %s.",
                normalized_symbol,
            )

            raise ApplicationError(
                "Failed to fetch Alpha Vantage candles.",
                {
                    "provider": self.name,
                    "symbol": normalized_symbol,
                    "timeframe": interval,
                    "limit": limit,
                },
            ) from error

        # --------------------------------------------------------------
        # Validate response
        # --------------------------------------------------------------

        if not isinstance(
            response,
            dict,
        ):
            raise ApplicationError(
                "Invalid Alpha Vantage response.",
                {
                    "provider": self.name,
                    "symbol": normalized_symbol,
                },
            )

        # --------------------------------------------------------------
        # API errors / informational responses
        # --------------------------------------------------------------

        if "Error Message" in response:
            raise ApplicationError(
                "Alpha Vantage returned an API error.",
                {
                    "provider": self.name,
                    "symbol": normalized_symbol,
                    "message": str(
                        response.get(
                            "Error Message"
                        )
                    ),
                },
            )

        if "Information" in response:
            raise ApplicationError(
                "Alpha Vantage returned an informational response.",
                {
                    "provider": self.name,
                    "symbol": normalized_symbol,
                    "message": str(
                        response.get(
                            "Information"
                        )
                    ),
                },
            )

        if "Note" in response:
            logger.warning(
                "Alpha Vantage rate-limit response "
                "for %s: %s",
                normalized_symbol,
                response.get("Note"),
            )

            return []

        # --------------------------------------------------------------
        # Locate time series
        # --------------------------------------------------------------

        time_series = self._find_time_series(
            response
        )

        candles: list[Candle] = []

        # --------------------------------------------------------------
        # Convert individual candles
        # --------------------------------------------------------------

        for (
            timestamp_text,
            values,
        ) in time_series.items():

            candle = self._convert_candle(
                symbol=normalized_symbol,
                timestamp_text=timestamp_text,
                values=values,
            )

            if candle is not None:
                candles.append(
                    candle
                )

        # --------------------------------------------------------------
        # Chronological order
        # --------------------------------------------------------------

        candles.sort(
            key=lambda candle: candle.timestamp
        )

        # --------------------------------------------------------------
        # Apply requested limit
        # --------------------------------------------------------------

        if len(candles) > limit:
            candles = candles[
                -limit:
            ]

        # --------------------------------------------------------------
        # Final validation through the common provider contract
        # --------------------------------------------------------------

        try:
            candles = self.validate_candles(
                candles
            )

        except Exception as error:
            logger.exception(
                "Alpha Vantage produced invalid "
                "standardized candles."
            )

            raise ApplicationError(
                "Alpha Vantage returned invalid standardized candles.",
                {
                    "provider": self.name,
                    "symbol": normalized_symbol,
                    "timeframe": interval,
                },
            ) from error

        logger.info(
            "Alpha Vantage returned %d valid candles "
            "for %s (%s).",
            len(candles),
            normalized_symbol,
            interval,
        )

        return candles


__all__ = [
    "AlphaVantageProvider",
]

