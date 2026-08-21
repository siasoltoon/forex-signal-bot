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
    Production-grade Finnhub market data provider.
    """

    name = "finnhub"

    _TIMEFRAME_ALIASES: Final[dict[str, str]] = {
        "M1": "1",
        "M5": "5",
        "M15": "15",
        "M30": "30",
        "H1": "60",
        "D": "D",
        "1D": "D",
        "W": "W",
        "1W": "W",
        "M": "M",
        "1M": "M",
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

    _MAX_LIMIT: Final[int] = 5000

    def __init__(
        self,
        client: FinnhubClient | None = None,
    ) -> None:
        self.client = (
            client
            if client is not None
            else FinnhubClient()
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

        return cls._TIMEFRAME_ALIASES.get(
            normalized,
            normalized,
        )

    @classmethod
    def _validate_timeframe(
        cls,
        timeframe: str,
    ) -> str:
        normalized = cls._normalize_timeframe(
            timeframe
        )

        if normalized not in cls._TIMEFRAME_MINUTES:
            raise ValueError(
                f"Unsupported Finnhub timeframe: "
                f"{timeframe}"
            )

        return normalized

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

        if limit > FinnhubProvider._MAX_LIMIT:
            raise ValueError(
                f"limit cannot exceed "
                f"{FinnhubProvider._MAX_LIMIT}."
            )

    @classmethod
    def _calculate_time_range(
        cls,
        timeframe: str,
        limit: int,
    ) -> tuple[int, int]:
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

    @staticmethod
    def _parse_timestamp(
        value: object,
    ) -> datetime:
        timestamp = int(value)

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
        volume = float(value)

        if volume < 0:
            raise ValueError(
                "Volume cannot be negative."
            )

        return volume

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
        try:
            return Candle(
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

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> list[Candle]:
        """
        Fetch and normalize Finnhub candles.
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

        resolution = self._validate_timeframe(
            timeframe
        )

        (
            from_timestamp,
            to_timestamp,
        ) = self._calculate_time_range(
            timeframe=resolution,
            limit=limit,
        )

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

        if response is None:
            logger.warning(
                "Finnhub returned no candle data "
                "for %s.",
                normalized_symbol,
            )

            return []

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

        status = response.get("s")

        if status != "ok":
            logger.warning(
                "Finnhub returned non-ok status: %s",
                status,
            )

            return []

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
                    "provider": self.name,
                    "symbol": normalized_symbol,
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
                    "provider": self.name,
                    "symbol": normalized_symbol,
                },
            )

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

        candles.sort(
            key=lambda candle: candle.timestamp
        )

        if len(candles) > limit:
            candles = candles[-limit:]

        logger.info(
            "Finnhub returned %d valid candles "
            "for %s.",
            len(candles),
            normalized_symbol,
        )

        return candles
