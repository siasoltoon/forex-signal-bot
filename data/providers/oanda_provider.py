from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
from typing import Final, Any

from core.errors import ApplicationError
from core.logger import setup_logger

from data.base import MarketDataProvider
from data.models import Candle
from data.providers.clients.oanda import OandaClient


logger = setup_logger()


class OandaProvider(MarketDataProvider):
    """Production-grade OANDA market data provider."""

    name = "oanda"

    _TIMEFRAME_ALIASES: Final[dict[str, str]] = {
        "M1": "M1", "M2": "M2", "M4": "M4", "M5": "M5",
        "M10": "M10", "M15": "M15", "M30": "M30",
        "H1": "H1", "H2": "H2", "H3": "H3", "H4": "H4",
        "H6": "H6", "H8": "H8", "H12": "H12",
        "D": "D", "W": "W", "M": "M",
    }

    def __init__(self, client: OandaClient | None = None) -> None:
        self.client = client if client is not None else OandaClient()

    @classmethod
    def _normalize_timeframe(cls, timeframe: str) -> str:
        """Normalize a timeframe using the common contract, then enforce OANDA support."""
        normalized = cls.normalize_timeframe(timeframe)
        result = cls._TIMEFRAME_ALIASES.get(normalized)
        if result is None:
            raise ValueError(f"Unsupported OANDA timeframe: {timeframe}")
        return result

    @staticmethod
    def _parse_timestamp(value: object) -> datetime:
        if not isinstance(value, str):
            raise TypeError("OANDA candle timestamp must be a string.")
        timestamp_text = value.strip()
        if not timestamp_text:
            raise ValueError("OANDA candle timestamp cannot be empty.")
        if timestamp_text.endswith("Z"):
            timestamp_text = timestamp_text[:-1] + "+00:00"
        timestamp = datetime.fromisoformat(timestamp_text)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        return timestamp.astimezone(timezone.utc)

    @staticmethod
    def _parse_price(value: object) -> float:
        try:
            price = float(value)
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError("Price must be a valid number.") from error
        if not isfinite(price):
            raise ValueError("Price must be finite.")
        if price <= 0:
            raise ValueError("Price must be greater than zero.")
        return price

    @staticmethod
    def _parse_volume(value: object) -> float:
        if value is None:
            return 0.0
        try:
            volume = float(value)
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError("Volume must be a valid number.") from error
        if not isfinite(volume):
            raise ValueError("Volume must be finite.")
        if volume < 0:
            raise ValueError("Volume cannot be negative.")
        return volume

    @staticmethod
    def _validate_ohlc(
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
    ) -> None:
        if high_price < low_price:
            raise ValueError("High price cannot be lower than low price.")
        if high_price < max(open_price, close_price):
            raise ValueError(
                "High price must be greater than or equal to open and close."
            )
        if low_price > min(open_price, close_price):
            raise ValueError(
                "Low price must be lower than or equal to open and close."
            )

    def _convert_candle(self, item: object, symbol: str) -> Candle | None:
        if not isinstance(item, dict):
            logger.warning("Skipping invalid OANDA candle payload.")
            return None
        if not item.get("complete", False):
            return None

        price = item.get("mid")
        if not isinstance(price, dict):
            logger.warning("Skipping OANDA candle without mid prices.")
            return None

        try:
            timestamp = self._parse_timestamp(item.get("time"))
            open_price = self._parse_price(price["o"])
            high_price = self._parse_price(price["h"])
            low_price = self._parse_price(price["l"])
            close_price = self._parse_price(price["c"])
            volume = self._parse_volume(item.get("volume", 0))
            self._validate_ohlc(open_price, high_price, low_price, close_price)
            return Candle(
                symbol=symbol,
                timestamp=timestamp,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
            )
        except (KeyError, TypeError, ValueError, OverflowError) as error:
            logger.warning("Skipping invalid OANDA candle: %s", error)
            return None

    @staticmethod
    def _extract_candles(response: object, symbol: str) -> list[Any]:
        if not isinstance(response, dict):
            raise ApplicationError(
                "Invalid OANDA response.",
                {"provider": "oanda", "symbol": symbol},
            )
        raw_candles = response.get("candles")
        if raw_candles is None:
            raise ApplicationError(
                "OANDA response does not contain candles.",
                {"provider": "oanda", "symbol": symbol},
            )
        if not isinstance(raw_candles, list):
            raise ApplicationError(
                "Invalid OANDA candles payload.",
                {"provider": "oanda", "symbol": symbol},
            )
        return raw_candles

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = MarketDataProvider.DEFAULT_LIMIT,
    ) -> list[Candle]:
        """Fetch and normalize OANDA candles using the common provider contract."""
        self.validate_request(symbol, timeframe, limit)
        normalized_symbol = self.normalize_symbol(symbol)
        normalized_timeframe = self._normalize_timeframe(timeframe)

        try:
            response = await self.client.get_candles(
                instrument=normalized_symbol,
                granularity=normalized_timeframe,
                count=limit,
            )
        except Exception as error:
            logger.exception("OANDA candle request failed for %s.", normalized_symbol)
            raise ApplicationError(
                "Failed to fetch OANDA candles.",
                {
                    "provider": self.name,
                    "symbol": normalized_symbol,
                    "timeframe": normalized_timeframe,
                    "limit": limit,
                },
            ) from error

        raw_candles = self._extract_candles(response, normalized_symbol)
        candles: list[Candle] = []
        for item in raw_candles:
            candle = self._convert_candle(item, normalized_symbol)
            if candle is not None:
                candles.append(candle)

        candles = self.normalize_candles(
            candles,
            expected_symbol=normalized_symbol,
            deduplicate=True,
        )
        candles = self.apply_limit(candles, limit)

        logger.info(
            "OANDA returned %d valid candles for %s (%s).",
            len(candles),
            normalized_symbol,
            normalized_timeframe,
        )
        return candles


__all__ = ["OandaProvider"]
