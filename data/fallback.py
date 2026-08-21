from __future__ import annotations

from core.errors import ApplicationError
from core.logger import setup_logger

from data.base import MarketDataProvider
from data.models import Candle


logger = setup_logger()


class FallbackProvider:
    """
    Tries multiple market data providers
    until one succeeds.
    """

    def __init__(
        self,
        providers: list[MarketDataProvider],
    ) -> None:

        if not providers:
            raise ValueError(
                "providers list cannot be empty."
            )

        self.providers = providers


    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> list[Candle]:
        """
        Fetch candles using provider fallback.
        """

        errors: list[str] = []


        for provider in self.providers:

            try:
                logger.info(
                    "Trying market provider: %s",
                    provider.name,
                )

                candles = await provider.get_candles(
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=limit,
                )


                if candles:
                    logger.info(
                        "Provider %s succeeded.",
                        provider.name,
                    )

                    return candles


                logger.warning(
                    "Provider %s returned empty candles.",
                    provider.name,
                )


            except Exception as error:

                logger.exception(
                    "Provider %s failed.",
                    provider.name,
                )

                errors.append(
                    f"{provider.name}: {error}"
                )


        raise ApplicationError(
            "All market data providers failed.",
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "limit": limit,
                "errors": errors,
            },
        )
