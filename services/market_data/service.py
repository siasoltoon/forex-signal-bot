from __future__ import annotations

from data.manager import DataManager
from data.models import Candle

from core.errors import ApplicationError
from core.logger import setup_logger


logger = setup_logger()


class MarketDataService:
    """
    High level market data service.

    Responsibilities:
    - Provide clean interface for analysis engines.
    - Hide provider/data-manager complexity.
    - Validate market data requests.
    - Prepare candles for indicators and AI.
    """


    def __init__(
        self,
        data_manager: DataManager,
    ) -> None:

        self.data_manager = data_manager


    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
        provider_name: str | None = None,
    ) -> list[Candle]:
        """
        Get market candles.
        """

        self._validate_request(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )


        try:

            candles = await self.data_manager.get_candles(
                provider_name=provider_name,
                symbol=symbol,
                timeframe=timeframe,
                limit=limit,
            )


        except Exception as error:

            logger.exception(
                "MarketDataService failed."
            )

            raise ApplicationError(
                "Market data service failed.",
                {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "limit": limit,
                },
            ) from error


        if not candles:

            logger.warning(
                "No candles returned for %s",
                symbol,
            )

            return []


        return candles



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
                "symbol must be string."
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
                "timeframe must be string."
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
                "limit must be integer."
            )


        if limit < 1:

            raise ValueError(
                "limit must be greater than zero."
            )
