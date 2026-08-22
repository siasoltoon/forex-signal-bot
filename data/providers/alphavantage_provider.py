from __future__ import annotations

from datetime import datetime, timezone
from typing import Final

from core.errors import ApplicationError
from core.logger import setup_logger

from data.base import MarketDataProvider
from data.models import Candle
from data.providers.clients.alphavantage import AlphaVantageClient


logger = setup_logger()


class AlphaVantageProvider(MarketDataProvider):
    """Alpha Vantage implementation of the common market-data contract."""

    name = "alphavantage"

    _TIMEFRAME_TO_INTERVAL: Final[dict[str, str]] = {
        "M1": "1min",
        "M5": "5min",
        "M15": "15min",
        "M30": "30min",
        "H1": "60min",
    }

    _SUPPORTED_INTERVALS: Final[frozenset[str]] = frozenset(
        _TIMEFRAME_TO_INTERVAL.values()
    )

    def __init__(self, client: AlphaVantageClient | None = None) -> None:
        self.client = client if client is not None else AlphaVantageClient()

    def is_configured(self) -> bool:
        """Return whether an Alpha Vantage API key is configured."""
        api_key = getattr(self.client, "api_key", None)
        return bool(api_key and str(api_key).strip())

    @classmethod
    def _normalize_timeframe(cls, timeframe: str) -> str:
        """Map the canonical project timeframe to Alpha Vantage interval."""
        canonical = cls.normalize_timeframe(timeframe)
        interval = cls._TIMEFRAME_TO_INTERVAL.get(canonical)
        if interval is None:
            raise ValueError(
                f"Unsupported Alpha Vantage timeframe: {timeframe!r}"
            )
        return interval

    @classmethod
    def _normalize_symbol(cls, symbol: str) -> str:
        """Use the common semantic symbol normalization."""
        return cls.normalize_symbol(symbol)

    @staticmethod
    def _parse_timestamp(value: object) -> datetime:
        if not isinstance(value, str):
            raise TypeError("Alpha Vantage timestamp must be a string.")

        text = value.strip()
        if not text:
            raise ValueError("Alpha Vantage timestamp cannot be empty.")

        for timestamp_format in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
        ):
            try:
                return datetime.strptime(text, timestamp_format).replace(
                    tzinfo=timezone.utc
                )
            except ValueError:
                continue

        raise ValueError(
            f"Unsupported Alpha Vantage timestamp format: {value!r}"
        )

    @staticmethod
    def _parse_price(value: object) -> float:
        try:
            price = float(value)
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError("Price must be numeric.") from error

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
            raise ValueError("Volume must be numeric.") from error

        if volume < 0:
            raise ValueError("Volume cannot be negative.")
        return volume

    @classmethod
    def _find_time_series(cls, response: dict[str, object]) -> dict[str, object]:
        """Locate Alpha Vantage's time-series object in the response."""
        for key, value in response.items():
            if (
                isinstance(key, str)
                and key.lower().startswith("time series")
                and isinstance(value, dict)
            ):
                return value

        raise ApplicationError(
            "Alpha Vantage time series was not found.",
            {"provider": cls.name},
        )

    @staticmethod
    def _convert_candle(
        symbol: str,
        timestamp_text: object,
        values: object,
    ) -> Candle | None:
        """Convert one Alpha Vantage record into a standard Candle."""
        if not isinstance(values, dict):
            logger.warning("Skipping invalid Alpha Vantage candle payload.")
            return None

        try:
            return Candle(
                symbol=symbol,
                timestamp=AlphaVantageProvider._parse_timestamp(timestamp_text),
                open=AlphaVantageProvider._parse_price(values["1. open"]),
                high=AlphaVantageProvider._parse_price(values["2. high"]),
                low=AlphaVantageProvider._parse_price(values["3. low"]),
                close=AlphaVantageProvider._parse_price(values["4. close"]),
                volume=AlphaVantageProvider._parse_volume(
                    values.get("5. volume", 0)
                ),
            )
        except (KeyError, TypeError, ValueError, OverflowError) as error:
            logger.warning("Skipping invalid Alpha Vantage candle: %s", error)
            return None

    @staticmethod
    def _raise_api_error(
        response: dict[str, object],
        symbol: str,
    ) -> None:
        if "Error Message" in response:
            raise ApplicationError(
                "Alpha Vantage returned an API error.",
                {
                    "provider": "alphavantage",
                    "symbol": symbol,
                    "message": str(response.get("Error Message")),
                },
            )

        if "Information" in response:
            raise ApplicationError(
                "Alpha Vantage returned an informational response.",
                {
                    "provider": "alphavantage",
                    "symbol": symbol,
                    "message": str(response.get("Information")),
                },
            )

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = MarketDataProvider.DEFAULT_LIMIT,
    ) -> list[Candle]:
        """Fetch and return standardized Alpha Vantage candles."""
        self.validate_request(symbol, timeframe, limit)

        normalized_symbol = self._normalize_symbol(symbol)
        interval = self._normalize_timeframe(timeframe)

        try:
            response = await self.client.get_intraday(
                symbol=normalized_symbol,
                interval=interval,
            )
        except Exception as error:
            logger.exception(
                "Alpha Vantage candle request failed for %s.",
                normalized_symbol,
            )
            raise ApplicationError(
                "Failed to fetch Alpha Vantage candles.",
                {
                    "provider": self.name,
                    "symbol": normalized_symbol,
                    "timeframe": interval,
                    "limit": limit,
                },
            ) from error

        if not isinstance(response, dict):
            raise ApplicationError(
                "Invalid Alpha Vantage response.",
                {
                    "provider": self.name,
                    "symbol": normalized_symbol,
                },
            )

        self._raise_api_error(response, normalized_symbol)

        if "Note" in response:
            logger.warning(
                "Alpha Vantage rate-limit response for %s: %s",
                normalized_symbol,
                response.get("Note"),
            )
            return []

        time_series = self._find_time_series(response)
        candles: list[Candle] = []

        for timestamp_text, values in time_series.items():
            candle = self._convert_candle(
                symbol=normalized_symbol,
                timestamp_text=timestamp_text,
                values=values,
            )
            if candle is not None:
                candles.append(candle)

        candles = self.normalize_candles(
            candles,
            expected_symbol=normalized_symbol,
            deduplicate=True,
        )
        candles = self.apply_limit(candles, limit)

        try:
            candles = self.validate_candles(
                candles,
                expected_symbol=normalized_symbol,
                require_sorted=True,
                reject_duplicates=True,
            )
        except (TypeError, ValueError) as error:
            logger.exception(
                "Alpha Vantage produced invalid standardized candles."
            )
            raise ApplicationError(
                "Alpha Vantage returned invalid standardized candles.",
                {
                    "provider": self.name,
                    "symbol": normalized_symbol,
                    "timeframe": interval,
                },
            ) from error

        logger.info(
            "Alpha Vantage returned %d valid candles for %s (%s).",
            len(candles),
            normalized_symbol,
            interval,
        )
        return candles


__all__ = ["AlphaVantageProvider"]
