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
    Finnhub market data provider.

    Converts Finnhub candle responses into
    the application's standard Candle model.
    """

    name = "finnhub"

    _TIMEFRAME_MINUTES: Final[dict[str, int]] = {
        "1": 1,
        "5": 5,
        "15": 15,
        "30": 30,
        "60": 60,
    }

    _TIMEFRAME_ALIASES: Final[dict[str, str]] = {
        "M1": "1",
        "M5": "5",
        "M15": "15",
        "M30": "30",
        "H1": "60",
    }

    def __init__(self) -> None:
        self.client = FinnhubClient()

    def _normalize_timeframe(
        self,
        timeframe: str,
    ) -> str:
        normalized = timeframe.strip().upper()

        return self._TIMEFRAME_ALIASES.get(
            normalized,
            normalized,
        )

    def _calculate_time_range(
        self,
        timeframe: str,
        limit: int,
    ) -> tuple[int, int]:
        resolution = self._normalize_timeframe(
            timeframe
        )

        minutes = self._TIMEFRAME_MINUTES.get(
            resolution
        )

        if minutes is None:
            raise ValueError(
                f"Unsupported Finnhub timeframe: {timeframe}"
            )

        now = datetime.now(
            timezone.utc
        )

        seconds = (
            minutes
            * 60
            * limit
        )

        start = int(
            now.timestamp()
        ) - seconds

        end = int(
            now.timestamp()
        )

        return start, end

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> list[Candle]:
        """
        Fetch candles from Finnhub
        and convert them into Candle models.
        """

        if not symbol:
            raise ValueError(
                "symbol cannot be empty."
            )

        if not timeframe:
            raise ValueError(
                "timeframe cannot be empty."
            )

        if limit < 1:
            raise ValueError(
                "limit must be greater than zero."
            )

        resolution = self._normalize_timeframe(
            timeframe
        )

        from_timestamp, to_timestamp = (
            self._calculate_time_range(
                resolution,
                limit,
            )
        )

        try:
            response = await self.client.get_candles(
                symbol=symbol,
                resolution=resolution,
                from_timestamp=from_timestamp,
                to_timestamp=to_timestamp,
            )

        except Exception as error:
            logger.exception(
                "Finnhub candle request failed."
            )

            raise ApplicationError(
                "Failed to fetch Finnhub candles.",
                {
                    "provider": self.name,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "limit": limit,
                },
            ) from error

        if response is None:
            return []

        if not isinstance(
            response,
            dict,
        ):
            raise ApplicationError(
                "Invalid Finnhub response.",
                {
                    "provider": self.name,
                    "symbol": symbol,
                },
            )

        timestamps = response.get("t", [])
        opens = response.get("o", [])
        highs = response.get("h", [])
        lows = response.get("l", [])
        closes = response.get("c", [])
        volumes = response.get("v", [])

        if not all(
            isinstance(value, list)
            for value in (
                timestamps,
                opens,
                highs,
                lows,
                closes,
                volumes,
            )
        ):
            raise ApplicationError(
                "Invalid Finnhub candle payload.",
                {
                    "provider": self.name,
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
                    "provider": self.name,
                    "symbol": symbol,
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
            try:
                candle = Candle(
                    symbol=symbol,
                    timestamp=datetime.fromtimestamp(
                        int(timestamp),
                        tz=timezone.utc,
                    ),
                    open=float(open_price),
                    high=float(high),
                    low=float(low),
                    close=float(close),
                    volume=float(volume),
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
                continue

            candles.append(
                candle
            )

        if len(candles) > limit:
            candles = candles[-limit:]

        logger.info(
            "Finnhub returned %d valid candles for %s.",
            len(candles),
            symbol,
        )

        return candles
