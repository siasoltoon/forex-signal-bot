
from __future__ import annotations

from datetime import datetime, timezone

from data.base import MarketDataProvider
from data.models import Candle

from data.providers.clients.oanda import OandaClient

from core.errors import ApplicationError
from core.logger import setup_logger


logger = setup_logger()


class OandaProvider(
    MarketDataProvider
):
    """
    OANDA market data provider.
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
        Fetch candles from OANDA
        and convert them into Candle models.
        """


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
                    "symbol": symbol,
                    "timeframe": timeframe,
                },
            ) from error



        candles: list[Candle] = []


        for item in response.get(
            "candles",
            []
        ):

            if not item.get(
                "complete",
                False,
            ):
                continue


            price = item.get(
                "mid",
                {}
            )


            try:

                candle = Candle(

                    symbol=symbol,


                    timestamp=datetime.fromisoformat(
                        item["time"]
                        .replace(
                            "Z",
                            "+00:00"
                        )
                    ),


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
                            0
                        )
                    ),
                )


                candles.append(
                    candle
                )


            except (
                KeyError,
                ValueError,
                TypeError,
            ):

                logger.warning(
                    "Invalid OANDA candle skipped: %s",
                    item,
                )


        logger.info(
            "Loaded %d candles from OANDA for %s",
            len(candles),
            symbol,
        )


        return candles
