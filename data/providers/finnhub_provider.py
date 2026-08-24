from __future__ import annotations

from datetime import datetime, timezone
from typing import Final

from core.errors import ApplicationError
from core.logger import setup_logger
from data.base import MarketDataProvider
from data.models import Candle
from data.providers.clients.finnhub import FinnhubClient

logger = setup_logger()


class FinnhubProvider(MarketDataProvider):
    """Finnhub FOREX implementation of the common market-data contract."""

    name = "finnhub"
    _TIMEFRAME_ALIASES: Final[dict[str, str]] = {"M1":"1","1M":"1","M5":"5","5M":"5","M15":"15","15M":"15","M30":"30","30M":"30","H1":"60","1H":"60","D":"D","W":"W","M":"M"}
    _TIMEFRAME_MINUTES: Final[dict[str, int]] = {"1":1,"5":5,"15":15,"30":30,"60":60,"D":1440,"W":10080,"M":43200}

    def __init__(self, client: FinnhubClient | None = None) -> None:
        self.client = client if client is not None else FinnhubClient()

    def is_configured(self) -> bool:
        return self.client.is_configured()

    @classmethod
    def _normalize_timeframe(cls, timeframe: str) -> str:
        if not isinstance(timeframe, str) or not timeframe.strip():
            raise ValueError("timeframe cannot be empty")
        normalized = timeframe.strip().upper().replace(" ", "")
        aliases = {"1MIN":"1","5MIN":"5","15MIN":"15","30MIN":"30","1H":"60","1HR":"60","1DAY":"D","1WEEK":"W","1MONTH":"M"}
        return aliases.get(normalized, cls._TIMEFRAME_ALIASES.get(normalized, normalized))

    @classmethod
    def _validate_timeframe(cls, timeframe: str) -> str:
        resolution = cls._normalize_timeframe(timeframe)
        if resolution not in cls._TIMEFRAME_MINUTES:
            raise ValueError(f"Unsupported Finnhub timeframe: {timeframe!r}")
        return resolution

    @classmethod
    def _calculate_time_range(cls, timeframe: str, limit: int) -> tuple[int, int]:
        resolution = cls._validate_timeframe(timeframe)
        end = int(datetime.now(timezone.utc).timestamp())
        return end - cls._TIMEFRAME_MINUTES[resolution] * 60 * limit, end

    @staticmethod
    def _parse_timestamp(value: object) -> datetime:
        timestamp = int(value)
        if timestamp <= 0:
            raise ValueError("Finnhub timestamp must be positive")
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)

    @staticmethod
    def _parse_price(value: object) -> float:
        price = float(value)
        if price <= 0:
            raise ValueError("Price must be greater than zero")
        return price

    @staticmethod
    def _parse_volume(value: object) -> float:
        volume = 0.0 if value is None else float(value)
        if volume < 0:
            raise ValueError("Volume cannot be negative")
        return volume

    @staticmethod
    def _extract_arrays(response: dict) -> tuple[list, list, list, list, list, list]:
        arrays = tuple(response.get(key, []) for key in ("t","o","h","l","c","v"))
        if not all(isinstance(value, list) for value in arrays) or len({len(value) for value in arrays}) != 1:
            raise ApplicationError("Invalid Finnhub forex candle payload.", {"provider":"finnhub"})
        return arrays

    @staticmethod
    def _finnhub_forex_symbol(symbol: str) -> str:
        normalized = symbol.strip().upper().replace("/", "_")
        if normalized.startswith("OANDA:"):
            return normalized
        if len(normalized) == 6 and normalized.isalpha():
            normalized = f"{normalized[:3]}_{normalized[3:]}"
        return f"OANDA:{normalized}"

    async def get_candles(self, symbol: str, timeframe: str, limit: int = MarketDataProvider.DEFAULT_LIMIT) -> list[Candle]:
        self.validate_request(symbol, timeframe, limit)
        canonical_symbol = self.normalize_symbol(symbol)
        resolution = self._validate_timeframe(timeframe)
        start, end = self._calculate_time_range(resolution, limit)
        provider_symbol = self._finnhub_forex_symbol(canonical_symbol)
        try:
            response = await self.client.get_candles(provider_symbol, resolution, start, end)
        except Exception as error:
            raise ApplicationError("Failed to fetch Finnhub forex candles.", {"provider":self.name,"symbol":canonical_symbol,"timeframe":resolution}) from error
        if not response or response.get("s") != "ok":
            return []
        timestamps, opens, highs, lows, closes, volumes = self._extract_arrays(response)
        candles: list[Candle] = []
        for values in zip(timestamps, opens, highs, lows, closes, volumes):
            try:
                candles.append(Candle(symbol=canonical_symbol, timestamp=self._parse_timestamp(values[0]), open=self._parse_price(values[1]), high=self._parse_price(values[2]), low=self._parse_price(values[3]), close=self._parse_price(values[4]), volume=self._parse_volume(values[5])))
            except (TypeError, ValueError, OverflowError):
                continue
        return self.validate_candles(self.normalize_candles(candles, expected_symbol=canonical_symbol, deduplicate=True), expected_symbol=canonical_symbol, require_sorted=True, reject_duplicates=True)


__all__ = ["FinnhubProvider"]
