import logging
from typing import Any, Optional

import httpx

from config.settings import settings


logger = logging.getLogger(__name__)


class FinnhubClient:
    """
    Async client for the Finnhub API.
    """

    BASE_URL = "https://finnhub.io/api/v1"

    def __init__(self) -> None:
        self.api_key = settings.FINNHUB_API_KEY

    def _check_api_key(self) -> None:
        if not self.api_key:
            raise RuntimeError(
                "FINNHUB_API_KEY is not configured."
            )

    async def get_quote(
        self,
        symbol: str,
    ) -> dict[str, Any]:
        """
        Get the latest quote for a symbol.
        """

        self._check_api_key()

        url = f"{self.BASE_URL}/quote"

        params = {
            "symbol": symbol,
            "token": self.api_key,
        }

        async with httpx.AsyncClient(
            timeout=15.0
        ) as client:

            response = await client.get(
                url,
                params=params,
            )

            response.raise_for_status()

            data = response.json()

        return data

    async def get_candles(
        self,
        symbol: str,
        resolution: str,
        from_timestamp: int,
        to_timestamp: int,
    ) -> Optional[dict[str, Any]]:
        """
        Get historical candle data.

        resolution examples:
        1, 5, 15, 30, 60, D, W, M
        """

        self._check_api_key()

        url = f"{self.BASE_URL}/stock/candle"

        params = {
            "symbol": symbol,
            "resolution": resolution,
            "from": from_timestamp,
            "to": to_timestamp,
            "token": self.api_key,
        }

        async with httpx.AsyncClient(
            timeout=20.0
        ) as client:

            response = await client.get(
                url,
                params=params,
            )

            response.raise_for_status()

            data = response.json()

        if data.get("s") != "ok":
            logger.warning(
                "Finnhub returned non-ok candle status: %s",
                data.get("s"),
            )
            return None

        return data
