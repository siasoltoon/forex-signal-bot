import logging
from typing import Any
import httpx
from config.settings import settings

logger = logging.getLogger(__name__)


class AlphaVantageClient:
    """Async client for Alpha Vantage FX market data."""
    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self) -> None:
        self.api_key = settings.ALPHAVANTAGE_API_KEY

    def _check_api_key(self) -> None:
        if not self.api_key:
            raise RuntimeError("ALPHAVANTAGE_API_KEY is not configured.")

    def is_configured(self) -> bool:
        return bool(self.api_key and str(self.api_key).strip())

    async def get_forex_quote(self, from_currency: str, to_currency: str) -> dict[str, Any]:
        self._check_api_key()
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(self.BASE_URL, params={"function":"CURRENCY_EXCHANGE_RATE","from_currency":from_currency,"to_currency":to_currency,"apikey":self.api_key})
            response.raise_for_status()
            return response.json()

    async def get_forex_intraday(self, from_currency: str, to_currency: str, interval: str = "15min") -> dict[str, Any]:
        """Fetch real FX intraday candles using Alpha Vantage FX_INTRADAY."""
        self._check_api_key()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.BASE_URL, params={"function":"FX_INTRADAY","from_symbol":from_currency,"to_symbol":to_currency,"interval":interval,"outputsize":"full","apikey":self.api_key})
            response.raise_for_status()
            data = response.json()
        if "Error Message" in data:
            raise RuntimeError(str(data["Error Message"]))
        if "Note" in data:
            logger.warning("Alpha Vantage rate-limit message: %s", data["Note"])
        return data

    async def get_intraday(self, symbol: str, interval: str = "15min") -> dict[str, Any]:
        """Backward-compatible stock/ETF endpoint."""
        self._check_api_key()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.BASE_URL, params={"function":"TIME_SERIES_INTRADAY","symbol":symbol,"interval":interval,"apikey":self.api_key})
            response.raise_for_status()
            return response.json()
