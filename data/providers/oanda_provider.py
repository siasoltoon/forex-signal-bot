from __future__ import annotations

from datetime import datetime

from core.errors import ApplicationError
from core.logger import setup_logger

from data.base import MarketDataProvider
from data.models import Candle
from data.providers.clients.oanda import OandaClient


logger = setup_logger()


class OandaProvider(MarketDataProvider):
    """
    OANDA market data provider.

    Responsibilities:
    - Request candle data through OandaClient.
    - Validate OANDA response.
    - Convert API candles into Candle models.
    - Ignore incomplete candles.
    """


    name = "oanda"


    def __init__(self) -> None:
        self.client = OandaClient()


    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> list[Candle]:
        """
        Fetch and normalize OANDA candles.
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

        try:
            response = await self.client.get_candles(
                instrument=symbol,
                granularity=timeframe,
                count=limit,
            )

        except Exception as error:
            logger.exception(
                "OANDA candle request failed."
            )

            raise ApplicationError(
                "Failed to fetch OANDA candles.",
                {
                    "provider": self.name,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "limit": limit,
                },
            ) from error

        if not isinstance(response, dict):
            raise ApplicationError(
                "Invalid OANDA response.",
                {
                    "provider": self.name,
                    "symbol": symbol,
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
                    "symbol": symbol,
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
                    "symbol": symbol,
                },
            )

        candles: list[Candle] = []

        for item in raw_candles:

            if not isinstance(
                item,
                dict,
            ):
                logger.warning(
                    "Skipping invalid OANDA candle."
                )
                continue

            if not item.get(
                "complete",
                False,
            ):
                continue

            price = item.get(
                "mid"
            )

            if not isinstance(
                price,
                dict,
            ):
                logger.warning(
                    "Skipping OANDA candle "
                    "without mid prices."
                )
                continue

            try:
                timestamp = datetime.fromisoformat(
                    str(
                        item["time"]
                    ).replace(
                        "Z",
                        "+00:00",
                    )
                )

                candle = Candle(
                    symbol=symbol,
                    timestamp=timestamp,
                    open=float(
                        price["o"]
                    ),
                    high=float(
                        price["h"]
                    ),
                    low=float(
                        price["l"]
                    ),
                    close=float(
                        price["c"]
                    ),
                    volume=float(
                        item.get(
                            "volume",
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
                    "Skipping invalid OANDA candle: %s",
                    error,
                )

                continue

            candles.append(
                candle
            )

        logger.info(
            "OANDA returned %d valid candles "
            "for %s.",
            len(candles),
            symbol,
        )

        return candles
