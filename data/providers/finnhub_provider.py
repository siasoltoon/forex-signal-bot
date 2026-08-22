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
    """Finnhub implementation of the common market-data provider contract."""

    name = "finnhub"

    _TIMEFRAME_ALIASES: Final[dict[str, str]] = {
        "M1": "1", "1M": "1", "1MIN": "1", "1MINUTE": "1",
        "M5": "5", "5M": "5", "5MIN": "5", "5MINUTE": "5",
        "M15": "15", "15M": "15", "15MIN": "15", "15MINUTE": "15",
        "M30": "30", "30M": "30", "30MIN": "30", "30MINUTE": "30",
        "H1": "60", "1H": "60", "1HR": "60", "1HOUR": "60",
        "D": "D", "1D": "D", "1DAY": "D", "DAILY": "D",
        "W": "W", "1W": "W", "1WEEK": "W", "WEEKLY": "W",
        "M": "M", "1MONTH": "M", "MONTHLY": "M",
    }

    _TIMEFRAME_MINUTES: Final[dict[str, int]] = {
        "1": 1, "5": 5, "15": 15, "30": 30,
        "60": 60, "D": 1440, "W": 10080, "M": 43200,
    }

    _MAX_LIMIT: Final[int] = MarketDataProvider.MAX_LIMIT

    def __init__(self, client: FinnhubClient | None = None) -> None:
        self.client = client if client is not None else FinnhubClient()

    def is_configured(self) -> bool:
        checker = getattr(self.client, "is_configured", None)
        if callable(checker):
            try:
                return bool(checker())
            except Exception:
                logger.exception("Finnhub configuration check failed.")
                return False
        return True

    @classmethod
    def _normalize_timeframe(cls, timeframe: str) -> str:
        """Translate project timeframe notation into Finnhub resolution."""
        if not isinstance(timeframe, str):
            raise TypeError("timeframe must be a string.")
        raw = timeframe.strip().replace(" ", "")
        if not raw:
            raise ValueError("timeframe cannot be empty.")

        minute_aliases = {
            "1m": "1", "5m": "5", "15m": "15", "30m": "30",
            "1min": "1", "5min": "5", "15min": "15", "30min": "30",
            "1minute": "1", "5minute": "5", "15minute": "15", "30minute": "30",
        }
        if raw.lower() in minute_aliases:
            return minute_aliases[raw.lower()]

        normalized = raw.upper()
        return cls._TIMEFRAME_ALIASES.get(normalized, normalized)

    @classmethod
    def _validate_timeframe(cls, timeframe: str) -> str:
        normalized = cls._normalize_timeframe(timeframe)
        if normalized not in cls._TIMEFRAME_MINUTES:
            raise ValueError(f"Unsupported Finnhub timeframe: {timeframe!r}")
        return normalized

    @classmethod
    def _calculate_time_range(cls, timeframe: str, limit: int) -> tuple[int, int]:
        resolution = cls._validate_timeframe(timeframe)
        minutes = cls._TIMEFRAME_MINUTES[resolution]
        end_timestamp = int(datetime.now(timezone.utc).timestamp())
        start_timestamp = end_timestamp - (minutes * 60 * limit)
        return start_timestamp, end_timestamp

    @staticmethod
    def _parse_timestamp(value: object) -> datetime:
        try:
            timestamp = int(value)
        except (TypeError, ValueError) as error:
            raise ValueError("Finnhub timestamp must be an integer.") from error
        if timestamp <= 0:
            raise ValueError("Finnhub timestamp must be positive.")
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)

    @staticmethod
    def _parse_price(value: object) -> float:
        try:
            price = float(value)
        except (TypeError, ValueError) as error:
            raise ValueError("Finnhub price must be numeric.") from error
        if price <= 0:
            raise ValueError("Price must be greater than zero.")
        return price

    @staticmethod
    def _parse_volume(value: object) -> float:
        try:
            volume = float(value)
        except (TypeError, ValueError) as error:
            raise ValueError("Finnhub volume must be numeric.") from error
        if volume < 0:
            raise ValueError("Volume cannot be negative.")
        return volume

    def _convert_candle(self, symbol: str, timestamp: object, open_price: object,
                        high: object, low: object, close: object,
                        volume: object) -> Candle | None:
        try:
            return Candle(
                symbol=symbol,
                timestamp=self._parse_timestamp(timestamp),
                open=self._parse_price(open_price),
                high=self._parse_price(high),
                low=self._parse_price(low),
                close=self._parse_price(close),
                volume=self._parse_volume(volume),
            )
        except (TypeError, ValueError, OverflowError) as error:
            logger.warning("Skipping invalid Finnhub candle: %s", error)
            return None

    @staticmethod
    def _validate_response_structure(response: object, symbol: str) -> dict:
        if response is None:
            return {}
        if not isinstance(response, dict):
            raise ApplicationError(
                "Invalid Finnhub response.",
                {"provider": "finnhub", "symbol": symbol},
            )
        return response

    @staticmethod
    def _extract_arrays(response: dict, symbol: str) -> tuple[list, list, list, list, list, list]:
        arrays = (
            response.get("t", []), response.get("o", []), response.get("h", []),
            response.get("l", []), response.get("c", []), response.get("v", []),
        )
        if not all(isinstance(value, list) for value in arrays):
            raise ApplicationError(
                "Invalid Finnhub candle payload.",
                {"provider": "finnhub", "symbol": symbol},
            )
        if len({len(value) for value in arrays}) != 1:
            raise ApplicationError(
                "Finnhub candle arrays have inconsistent lengths.",
                {"provider": "finnhub", "symbol": symbol},
            )
        return arrays

    async def get_candles(self, symbol: str, timeframe: str,
                          limit: int = MarketDataProvider.DEFAULT_LIMIT) -> list[Candle]:
        """Fetch Finnhub candles and return canonical Candle objects."""
        self.validate_request(symbol, timeframe, limit)
        normalized_symbol = self.normalize_symbol(symbol)
        resolution = self._validate_timeframe(timeframe)
        from_timestamp, to_timestamp = self._calculate_time_range(resolution, limit)

        try:
            response = await self.client.get_candles(
                symbol=normalized_symbol,
                resolution=resolution,
                from_timestamp=from_timestamp,
                to_timestamp=to_timestamp,
            )
        except Exception as error:
            logger.exception("Finnhub candle request failed for %s.", normalized_symbol)
            raise ApplicationError(
                "Failed to fetch Finnhub candles.",
                {"provider": self.name, "symbol": normalized_symbol,
                 "timeframe": resolution, "limit": limit},
            ) from error

        if response is None:
            logger.warning("Finnhub returned no candle data for %s.", normalized_symbol)
            return []

        response = self._validate_response_structure(response, normalized_symbol)
        if not response or response.get("s") != "ok":
            logger.warning("Finnhub returned non-ok status for %s: %s",
                           normalized_symbol, response.get("s") if response else None)
            return []

        timestamps, opens, highs, lows, closes, volumes = self._extract_arrays(
            response, normalized_symbol
        )

        candles: list[Candle] = []
        for values in zip(timestamps, opens, highs, lows, closes, volumes):
            candle = self._convert_candle(
                normalized_symbol, values[0], values[1], values[2],
                values[3], values[4], values[5]
            )
            if candle is not None:
                candles.append(candle)

        candles = self.normalize_candles(
            candles, expected_symbol=normalized_symbol, deduplicate=True
        )
        candles = self.apply_limit(candles, limit)

        try:
            return self.validate_candles(
                candles,
                expected_symbol=normalized_symbol,
                require_sorted=True,
                reject_duplicates=True,
            )
        except Exception as error:
            logger.exception("Finnhub produced invalid standardized candles.")
            raise ApplicationError(
                "Finnhub returned invalid standardized candles.",
                {"provider": self.name, "symbol": normalized_symbol,
                 "timeframe": resolution},
            ) from error


__all__ = ["FinnhubProvider"]
