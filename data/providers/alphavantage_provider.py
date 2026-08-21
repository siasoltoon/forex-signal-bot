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
    Production-grade Alpha Vantage market data provider.

    Responsibilities:
    - Validate request parameters.
    - Normalize supported timeframes.
    - Request intraday data through AlphaVantageClient.
    - Validate Alpha Vantage responses.
    - Parse and normalize candle data.
    - Convert API data into Candle models.
    - Preserve chronological ordering.
    - Return at most `limit` candles.
    """

    name = "alphavantage"

    _TIMEFRAME_ALIASES: Final[
        dict[str, str]
    ] = {
        "M1": "1min",
        "1M": "1min",
        "M5": "5min",
        "M15": "15min",
        "M30": "30min",
        "H1": "60min",
    }

    _SUPPORTED_INTERVALS: Final[
        frozenset[str]
    ] = frozenset(
        {
            "1min",
            "5min",
            "15min",
            "30min",
            "60min",
        }
    )

    _MAX_LIMIT: Final[int] = 5000

    def __init__(
        self,
        client: AlphaVantageClient | None = None,
    ) -> None:
        self.client = (
            client
            if client is not None
            else AlphaVantageClient()
        )

    @classmethod
    def _normalize_timeframe(
        cls,
        timeframe: str,
    ) -> str:
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

        interval = cls._TIMEFRAME_ALIASES.get(
            normalized
        )

        if interval is None:
            raise ValueError(
                f"Unsupported Alpha Vantage timeframe: "
                f"{timeframe}"
            )

        return interval

    @classmethod
    def _validate_timeframe(
        cls,
        timeframe: str,
    ) -> str:
        interval = cls._normalize_timeframe(
            timeframe
        )

        if interval not in cls._SUPPORTED_INTERVALS:
            raise ValueError(
                f"Unsupported Alpha Vantage interval: "
                f"{interval}"
            )

        return interval

    @staticmethod
    def _validate_request(
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> None:
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

        if limit > AlphaVantageProvider._MAX_LIMIT:
            raise ValueError(
                f"limit cannot exceed "
                f"{AlphaVantageProvider._MAX_LIMIT}."
            )

    @staticmethod
    def _parse_timestamp(
        value: object,
    ) -> datetime:
        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                "Alpha Vantage timestamp "
                "must be a string."
            )

        timestamp_text = value.strip()

        timestamp = datetime.strptime(
            timestamp_text,
            "%Y-%m-%d %H:%M:%S",
        )

        return timestamp.replace(
            tzinfo=timezone.utc
        )

    @staticmethod
    def _parse_price(
        value: object,
    ) -> float:
        price = float(value)

        if price <= 0:
            raise ValueError(
                "Price must be greater than zero."
            )

        return price

    @staticmethod
    def _parse_volume(
        value: object,
    ) -> float:
        if value is None:
            return 0.0

        volume = float(value)

        if volume < 0:
            raise ValueError(
                "Volume cannot be negative."
            )

        return volume

    @classmethod
    def _find_time_series(
        cls,
        response: dict[str, object],
    ) -> dict[str, object]:
        for key, value in response.items():
            if (
                isinstance(key, str)
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

    def _convert_candle(
        self,
        symbol: str,
        timestamp_text: object,
        values: object,
    ) -> Candle | None:
        if not isinstance(
            values,
            dict,
        ):
            logger.warning(
                "Skipping invalid Alpha Vantage "
                "candle payload."
            )

            return None

        try:
            timestamp = self._parse_timestamp(
                timestamp_text
            )

            candle = Candle(
                symbol=symbol,
                timestamp=timestamp,
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
                "Skipping invalid Alpha Vantage "
                "candle: %s",
                error,
            )

            return None

        return candle

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> list[Candle]:
        """
        Fetch and normalize Alpha Vantage candles.
        """

        self._validate_request(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

        normalized_symbol = (
            symbol
            .strip()
            .upper()
        )

        interval = self._validate_timeframe(
            timeframe
        )

        try:
            response = (
                await self.client.get_intraday(
                    symbol=normalized_symbol,
                    interval=interval,
                )
            )

        except Exception as error:
            logger.exception(
                "Alpha Vantage candle request "
                "failed for %s.",
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

        if "Error Message" in response:
            raise ApplicationError(
                "Alpha Vantage returned an error.",
                {
                    "provider": self.name,
                    "symbol": normalized_symbol,
                    "error": response.get(
                        "Error Message"
                    ),
                },
            )

        if "Note" in response:
            logger.warning(
                "Alpha Vantage rate limit message: %s",
                response.get("Note"),
            )

        time_series = self._find_time_series(
            response
        )

       
