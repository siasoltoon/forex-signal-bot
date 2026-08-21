from __future__ import annotations

from datetime import datetime, timezone
from typing import Final

from core.errors import ApplicationError
from core.logger import setup_logger

from data.base import MarketDataProvider
from data.models import Candle
from data.providers.clients.oanda import OandaClient


logger = setup_logger()


class OandaProvider(MarketDataProvider):
    """
    Production-grade OANDA market data provider.

    Responsibilities:
    - Validate request parameters.
    - Normalize OANDA instrument/timeframe values.
    - Request candle data through OandaClient.
    - Validate the API response.
    - Ignore incomplete candles.
    - Convert valid candles into Candle models.
    - Preserve chronological ordering.
    - Return at most `limit` candles.
    """

    name = "oanda"

    _TIMEFRAME_ALIASES: Final[
        dict[str, str]
    ] = {
        "M1": "M1",
        "M2": "M2",
        "M4": "M4",
        "M5": "M5",
        "M10": "M10",
        "M15": "M15",
        "M30": "M30",
        "H1": "H1",
        "H2": "H2",
        "H3": "H3",
        "H4": "H4",
        "H6": "H6",
        "H8": "H8",
        "H12": "H12",
        "D": "D",
        "W": "W",
        "M": "M",
    }

    _MAX_LIMIT: Final[int] = 5000

    def __init__(
        self,
        client: OandaClient | None = None,
    ) -> None:

        self.client = (
            client
            if client is not None
            else OandaClient()
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

        result = cls._TIMEFRAME_ALIASES.get(
            normalized
        )

        if result is None:
            raise ValueError(
                f"Unsupported OANDA timeframe: "
                f"{timeframe}"
            )

        return result

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

        if limit > OandaProvider._MAX_LIMIT:
            raise ValueError(
                f"limit cannot exceed "
                f"{OandaProvider._MAX_LIMIT}."
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
                "OANDA candle timestamp "
                "must be a string."
            )

        timestamp_text = (
            value
            .strip()
            .replace(
                "Z",
                "+00:00",
            )
        )

        timestamp = (
            datetime.fromisoformat(
                timestamp_text
            )
        )

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(
                tzinfo=timezone.utc
            )

        return timestamp.astimezone(
            timezone.utc
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

    def _convert_candle(
        self,
        item: object,
        symbol: str,
    ) -> Candle | None:

        if not isinstance(
            item,
            dict,
        ):
            logger.warning(
                "Skipping invalid OANDA candle payload."
            )

            return None

        if not item.get(
            "complete",
            False,
        ):
            return None

        price = item.get(
            "mid"
        )

        if not isinstance(
            price,
            dict,
        ):
            logger.warning(
                "Skipping OANDA candle without "
                "mid prices."
            )

            return None

        try:
            timestamp = (
                self._parse_timestamp(
                    item.get("time")
                )
            )

            candle = Candle(
                symbol=symbol,
                timestamp=timestamp,
                open=self._parse_price(
                    price["o"]
                ),
                high=self._parse_price(
                    price["h"]
                ),
                low=self._parse_price(
                    price["l"]
                ),
                close=self._parse_price(
                    price["c"]
                ),
                volume=self._parse_volume(
                    item.get("volume", 0)
                ),
            )

        except (
            KeyError,
            TypeError,
            ValueError,
            OverflowError,
        ) as error:

            logger.warning(
                "Skipping invalid OANDA candle: %s",
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
        Fetch and normalize OANDA candles.
        """

        self._validate_request(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

        normalized_symbol = (
            symbol.strip().upper()
        )

        normalized_timeframe = (
            self._normalize_timeframe(
                timeframe
            )
        )

        try:
            response = (
                await self.client.get_candles(
                    instrument=normalized_symbol,
                    granularity=normalized_timeframe,
                    count=limit,
                )
            )

        except Exception as error:

            logger.exception(
                "OANDA candle request failed "
                "for %s.",
                normalized_symbol,
            )

            raise ApplicationError(
                "Failed to fetch OANDA candles.",
                {
                    "provider": self.name,
                    "symbol": normalized_symbol,
                    "timeframe": normalized_timeframe,
                    "limit": limit,
                },
            ) from error

        if not isinstance(
            response,
            dict,
        ):
            raise ApplicationError(
                "Invalid OANDA response.",
                {
                    "provider": self.name,
                    "symbol": normalized_symbol,
                },
            )

        raw_candles = response.get(
            "candles"
        )

        if raw_candles is None:
            raise ApplicationError(
                "OANDA response does not contain candles.",
                {
                    "provider": self.name,
                    "symbol": normalized_symbol,
                },
            )

        if not isinstance(
            raw_candles,
            list,
        ):
            raise ApplicationError(
                "Invalid OANDA candles payload.",
                {
                    "provider": self.name,
                    "symbol": normalized_symbol,
                },
            )

        candles: list[Candle] = []

        for item in raw_candles:

            candle = self._convert_candle(
                item=item,
                symbol=normalized_symbol,
            )

            if candle is not None:
                candles.append(
                    candle
                )

        candles.sort(
            key=lambda candle: candle.timestamp
        )

        if len(candles) > limit:
            candles = candles[-limit:]

        logger.info(
            "OANDA returned %d valid candles "
            "for %s.",
            len(candles),
            normalized_symbol,
        )

        return candles
