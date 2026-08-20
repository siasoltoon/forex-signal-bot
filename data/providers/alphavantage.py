import logging
from typing import Any

import httpx

from config.settings import settings


logger = logging.getLogger(__name__)


class AlphaVantageClient:
    """
    Async client for the Alpha Vantage API.
    """

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self) -> None:
        self.api_key = settings.ALPHAVANTAGE_API_KEY

    def _check_api_key(self) -> None:
        if not self.api_key:
            raise RuntimeError(
                "ALPHAVANTAGE_API_KEY is not configured."
            )

    async def get_forex_quote(
        self,
        from_currency: str,
        to_currency: str,
    ) -> dict[str, Any]:
        """
        Get the latest forex exchange rate.
        """

        self._check_api_key()

        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_currency,
            "to_currency": to_currency,
            "apikey": self.api_key,
        }

        async with httpx.AsyncClient(
            timeout=20.0
        ) as client:

            response = await client.get(
                self.BASE_URL,
                params=params,
            )

            response.raise_for_status()

            data = response.json()

        if "Error Message" in data:
            raise RuntimeError(
                data["Error Message"]
            )

        if "Note" in data:
            logger.warning(
                "Alpha Vantage rate-limit message: %s",
                data["Note"],
            )

        return data

    async def get_intraday(
        self,
        symbol: str,
        interval: str = "15min",
    ) -> dict[str, Any]:
        """
        Get intraday stock/ETF data.

        Example intervals:
        1min, 5min, 15min, 30min, 60min
        """

        self._check_api_key()

        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol,
            "interval": interval,
            "apikey": self.api_key,
        }

        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:

            response = await client.get(
                self.BASE_URL,
                params=params,
            )

            response.raise_for_status()

            data = response.json()

        if "Error Message" in data:
            raise RuntimeError(
                data["Error Message"]
            )

        if "Note" in data:
            logger.warning(
                "Alpha Vantage rate-limit message: %s",
                data["Note"],
            )

        return data
