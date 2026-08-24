import logging
from typing import Any, Optional
import httpx
from config.settings import settings

logger = logging.getLogger(__name__)

class FinnhubClient:
    """Async client for Finnhub market data."""
    BASE_URL = "https://finnhub.io/api/v1"

    def __init__(self) -> None:
        self.api_key = settings.FINNHUB_API_KEY

    def _check_api_key(self) -> None:
        if not self.api_key:
            raise RuntimeError("FINNHUB_API_KEY is not configured.")

    def is_configured(self) -> bool:
        return bool(self.api_key and str(self.api_key).strip())

    @staticmethod
    def _forex_symbol(symbol: str) -> str:
        normalized = symbol.strip().upper().replace("/", "_")
        if normalized.startswith("OANDA:"):
            return normalized
        if len(normalized) == 6 and normalized.isalpha():
            normalized = f"{normalized[:3]}_{normalized[3:]}"
        return f"OANDA:{normalized}"

    async def get_quote(self, symbol: str) -> dict[str, Any]:
        self._check_api_key()
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{self.BASE_URL}/quote", params={"symbol": symbol, "token": self.api_key})
            response.raise_for_status()
            return response.json()

    async def get_candles(self, symbol: str, resolution: str, from_timestamp: int, to_timestamp: int) -> Optional[dict[str, Any]]:
        self._check_api_key()
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(f"{self.BASE_URL}/forex/candle", params={"symbol": self._forex_symbol(symbol), "resolution": resolution, "from": from_timestamp, "to": to_timestamp, "token": self.api_key})
            response.raise_for_status()
            data = response.json()
        if data.get("s") != "ok":
            logger.warning("Finnhub returned non-ok forex candle status: %s", data.get("s"))
            return data
        return data
