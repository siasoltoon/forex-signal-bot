import logging
from typing import Any

import httpx

from config.settings import settings


logger = logging.getLogger(__name__)


class OandaClient:
    """
    Async client for OANDA REST API.
    """

    BASE_URL = (
        "https://api-fxpractice.oanda.com/v3"
    )

    def __init__(self) -> None:
        self.api_key = settings.OANDA_API_KEY

    def _check_api_key(self) -> None:
        if not self.api_key:
            raise RuntimeError(
                "OANDA_API_KEY is not configured."
            )

    def _headers(self) -> dict[str, str]:
        self._check_api_key()

        return {
            "Authorization": (
                f"Bearer {self.api_key}"
            ),
            "Content-Type": "application/json",
        }

    async def get_candles(
        self,
        instrument: str,
        granularity: str = "M15",
        count: int = 500,
    ) -> dict[str, Any]:
        """
        Get historical candlestick data.

        Examples:
        EUR_USD
        GBP_USD
        USD_JPY

        Granularity examples:
        M1, M5, M15, M30,
        H1, H4, D, W
        """

        url = (
            f"{self.BASE_URL}/instruments/"
            f"{instrument}/candles"
        )

        params = {
            "granularity": granularity,
            "count": count,
            "price": "M",
        }

        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:

            response = await client.get(
                url,
                headers=self._headers(),
                params=params,
            )

            response.raise_for_status()

            return response.json()

    async def get_price(
        self,
        instrument: str,
    ) -> dict[str, Any]:
        """
        Get current pricing information.
        """

        url = (
            f"{self.BASE_URL}/accounts/"
            f"pricing"
        )

        params = {
            "instruments": instrument,
        }

        async with httpx.AsyncClient(
            timeout=15.0
        ) as client:

            response = await client.get(
                url,
                headers=self._headers(),
                params=params,
            )

            response.raise_for_status()

            return response.json()
