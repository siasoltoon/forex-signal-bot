from __future__ import annotations

from abc import ABC, abstractmethod

from data.models import Candle


class MarketDataProvider(ABC):
    """
    Base market data provider.
    """


    name: str


    @abstractmethod
    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> list[Candle]:
        """
        Fetch market candles.
        """

        pass
