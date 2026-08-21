
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
    Alpha Vantage market data provider.

    Converts Alpha Vantage intraday
    responses into the application's
    standard Candle model.
    """

    name = "alphavantage"

    _TIMEFRAME_ALIASES: Final[dict[str, str]] = {
        "M1": "1min",
        "M5": "5min",
        "M15": "15min",
        "M30": "30min",
        "H1": "60min",
    }

    def __init__(self) -> None:
        self.client = AlphaVantageClient()

    def _normalize_timeframe(
        self,
        timeframe: str,
    ) -> str:
        normalized = timeframe.strip().upper()

        interval = self._TIMEFRAME_ALIASES.get(
            normalized
        )

        if interval is None:
            raise ValueError(
                f"Unsupported Alpha Vantage timeframe: "
                f"{timeframe}"
            )

        return interval

    @staticmethod
    def _find_time_series(
        response: dict[str, object],
    ) -> tuple[str, dict[str, dict[str, str]]]:
        for key, value in response.items():
            if (
                key.lower().startswith(
                    "time series"
                )
                and isinstance(value, dict)
            ):
                return (
                    key,
                    value,
                )

        raise ApplicationError(
            "Alpha Vantage time series was not found.",
            {
                "provider": "alphavantage",
            },
        )

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> list[Candle]:
        """
        Fetch intraday candles from Alpha Vantage.
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

        interval = self._normalize_timeframe(
            timeframe
        )

        try:
            response = await self.client.get_intraday(
                symbol=symbol,
                interval=interval,
            )

        except Exception as error:
            logger.exception(
                "Alpha Vantage candle request failed."
            )

            raise ApplicationError(
                "Failed to fetch Alpha Vantage candles.",
                {
                    "provider": self.name,
                    "symbol": symbol,
                    "timeframe": timeframe,
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
                    "symbol": symbol,
                },
            )

        if "Error Message" in response:
            raise ApplicationError(
                "Alpha Vantage returned an error.",
                {
                    "provider": self.name,
                    "symbol": symbol,
                    "error": response.get(
                        "Error Message"
                    ),
                },
            )

        _, time_series = self._find_time_series(
            response
        )

        candles: list[Candle] = []

        for timestamp_text, values in time_series.items():

            if not isinstance(
                values,
                dict,
            ):
                logger.warning(
                    "Skipping invalid Alpha Vantage candle."
                )
                continue

            try:
                timestamp = datetime.strptime(
                    timestamp_text,
                    "%Y-%m-%d %H:%M:%S",
                ).replace(
                    tzinfo=timezone.utc
                )

                candle = Candle(
                    symbol=symbol,
                    timestamp=timestamp,
                    open=float(
                        values["1. open"]
                    ),
                    high=float(
                        values["2. high"]
                    ),
                    low=float(
                        values["3. low"]
                    ),
                    close=float(
                        values["4. close"]
                    ),
                    volume=float(
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
            ) as error:

                logger.warning(
                    "Skipping invalid Alpha Vantage candle: %s",
                    error,
                )

                continue

            candles.append(
                candle
            )

        candles.sort(
            key=lambda candle: candle.timestamp
        )

        if len(candles) > limit:
            candles = candles[-limit:]

        logger.info(
            "Alpha Vantage returned %d valid candles "
            "for %s.",
            len(candles),
            symbol,
        )

        return candles
