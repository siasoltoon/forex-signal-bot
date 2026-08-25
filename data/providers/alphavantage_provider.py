from __future__ import annotations
from datetime import datetime, timezone
from typing import Final
from core.errors import ApplicationError
from core.logger import setup_logger
from data.base import MarketDataProvider
from data.models import Candle
from data.providers.clients.alphavantage import AlphaVantageClient

logger = setup_logger()


class AlphaVantageRateLimitError(ApplicationError):
    """Raised when Alpha Vantage rejects a request due to limits."""


class AlphaVantageProvider(MarketDataProvider):
    """Alpha Vantage FX_INTRADAY provider."""

    name = "alphavantage"
    _TIMEFRAME_TO_INTERVAL: Final[dict[str, str]] = {"M1":"1min","M5":"5min","M15":"15min","M30":"30min","H1":"60min"}

    def __init__(self, client: AlphaVantageClient | None = None) -> None:
        self.client = client if client is not None else AlphaVantageClient()

    def is_configured(self) -> bool:
        return self.client.is_configured()

    @classmethod
    def _normalize_timeframe(cls, timeframe: str) -> str:
        canonical = cls.normalize_timeframe(timeframe)
        interval = cls._TIMEFRAME_TO_INTERVAL.get(canonical)
        if interval is None:
            raise ValueError(f"Unsupported Alpha Vantage timeframe: {timeframe!r}")
        return interval

    @staticmethod
    def _split_symbol(symbol: str) -> tuple[str, str]:
        normalized = symbol.strip().upper().replace("/", "").replace("_", "")
        if len(normalized) != 6 or not normalized.isalpha():
            raise ValueError(f"Unsupported FX symbol: {symbol!r}")
        return normalized[:3], normalized[3:]

    @staticmethod
    def _parse_timestamp(value: object) -> datetime:
        text = str(value).strip()
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        raise ValueError(f"Unsupported Alpha Vantage timestamp: {value!r}")

    @staticmethod
    def _parse_price(value: object) -> float:
        price = float(value)
        if price <= 0:
            raise ValueError("Price must be greater than zero")
        return price

    @staticmethod
    def _find_time_series(response: dict[str, object], *, symbol: str, timeframe: str, limit: int) -> dict[str, object]:
        for key, value in response.items():
            if isinstance(key, str) and "time series fx" in key.lower() and isinstance(value, dict):
                return value
        raise ApplicationError("Alpha Vantage FX time series was not found.", {"provider":"alphavantage","symbol":symbol,"timeframe":timeframe,"limit":limit})

    async def get_candles(self, symbol: str, timeframe: str, limit: int = MarketDataProvider.DEFAULT_LIMIT) -> list[Candle]:
        self.validate_request(symbol, timeframe, limit)
        canonical = self.normalize_symbol(symbol)
        from_currency, to_currency = self._split_symbol(canonical)
        interval = self._normalize_timeframe(timeframe)

        try:
            response = await self.client.get_forex_intraday(from_currency, to_currency, interval)
        except Exception as error:
            raise ApplicationError("Failed to fetch Alpha Vantage FX candles.", {"provider":self.name,"symbol":canonical,"timeframe":interval,"limit":limit}) from error

        if not isinstance(response, dict):
            raise ApplicationError("Invalid Alpha Vantage response.", {"provider":self.name,"symbol":canonical,"timeframe":interval,"limit":limit})

        if "Information" in response or "Note" in response:
            message = response.get("Information") or response.get("Note")
            logger.warning("Alpha Vantage unavailable: %s", message)
            raise AlphaVantageRateLimitError("Alpha Vantage rate limit or premium endpoint restriction.", {"provider":self.name,"symbol":canonical,"reason":message})

        series = self._find_time_series(response, symbol=canonical, timeframe=interval, limit=limit)
        candles: list[Candle] = []
        for timestamp, values in series.items():
            if not isinstance(values, dict):
                continue
            try:
                candles.append(Candle(symbol=canonical, timestamp=self._parse_timestamp(timestamp), open=self._parse_price(values["1. open"]), high=self._parse_price(values["2. high"]), low=self._parse_price(values["3. low"]), close=self._parse_price(values["4. close"]), volume=0.0))
            except (KeyError, TypeError, ValueError, OverflowError):
                continue

        candles = self.normalize_candles(candles, expected_symbol=canonical, deduplicate=True)
        return self.validate_candles(self.apply_limit(candles, limit), expected_symbol=canonical, require_sorted=True, reject_duplicates=True)


__all__ = ["AlphaVantageProvider"]
