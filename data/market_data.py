from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

import pandas as pd

from data.factory import ProviderFactory
from data.models import Candle
from data.provider_manager import ProviderManager
from data.quality import DataQuality


logger = logging.getLogger(__name__)


class MarketDataEngine:
    """
    Unified market-data facade.

    Provider selection, retry, fallback and cooldown are delegated to
    ProviderManager. This class owns the application-facing representation
    and performs the final deterministic data-quality gate before candles
    enter downstream analysis.
    """

    def __init__(
        self,
        provider_manager: ProviderManager | None = None,
    ) -> None:
        self.provider_manager = (
            provider_manager
            if provider_manager is not None
            else ProviderManager()
        )
        self._oanda_provider: Any | None = None

    # ------------------------------------------------------------------
    # Validation / normalization
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_request(
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> tuple[str, str, int]:
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string.")
        if not symbol.strip():
            raise ValueError("symbol cannot be empty.")

        if not isinstance(timeframe, str):
            raise TypeError("timeframe must be a string.")
        if not timeframe.strip():
            raise ValueError("timeframe cannot be empty.")

        if isinstance(limit, bool) or not isinstance(limit, int):
            raise TypeError("limit must be an integer.")
        if limit < 1:
            raise ValueError("limit must be greater than zero.")

        return (
            symbol.strip().upper(),
            timeframe.strip().upper(),
            limit,
        )

    @staticmethod
    def _validate_candles(
        candles: list[Candle],
        *,
        expected_symbol: str,
    ) -> list[Candle]:
        """
        Apply the final quality gate to provider-manager output.

        Gap detection is intentionally not enabled here. FX markets have
        legitimate calendar gaps (for example weekends and market holidays),
        so a normal retrieval request must not reject an otherwise valid
        series merely because two consecutive candles are not adjacent.
        """
        try:
            return DataQuality.validate(
                candles,
                expected_symbol=expected_symbol,
            )
        except (TypeError, ValueError) as exc:
            logger.error(
                "Market data quality validation failed for %s: %s",
                expected_symbol,
                exc,
            )
            raise

    @staticmethod
    def _validate_dataframe(
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Validate and normalize an OHLCV DataFrame.

        The returned frame always has a UTC DatetimeIndex and the
        canonical columns: open, high, low, close, volume.
        """
        required = ["open", "high", "low", "close"]

        if dataframe is None or dataframe.empty:
            return pd.DataFrame(
                columns=[*required, "volume"],
                index=pd.DatetimeIndex([], tz="UTC"),
            )

        frame = dataframe.copy()

        if not isinstance(frame.index, pd.DatetimeIndex):
            if "timestamp" not in frame.columns:
                raise ValueError(
                    "Market data must have a DatetimeIndex or timestamp column."
                )
            frame["timestamp"] = pd.to_datetime(
                frame["timestamp"],
                utc=True,
                errors="coerce",
            )
            frame = frame.set_index("timestamp")
        else:
            frame.index = pd.to_datetime(
                frame.index,
                utc=True,
                errors="coerce",
            )

        missing = [column for column in required if column not in frame.columns]
        if missing:
            raise ValueError(f"Missing OHLC columns: {missing}")

        if "volume" not in frame.columns:
            frame["volume"] = 0.0

        for column in [*required, "volume"]:
            frame[column] = pd.to_numeric(
                frame[column],
                errors="coerce",
            )

        frame = frame.dropna(
            subset=[*required, "volume"],
        )

        frame = frame[
            (frame["open"] > 0)
            & (frame["high"] > 0)
            & (frame["low"] > 0)
            & (frame["close"] > 0)
            & (frame["volume"] >= 0)
            & (frame["high"] >= frame[["open", "close", "low"]].max(axis=1))
            & (frame["low"] <= frame[["open", "close", "high"]].min(axis=1))
        ]

        frame = frame[~frame.index.isna()]
        frame = frame[~frame.index.duplicated(keep="last")]
        frame = frame.sort_index()

        return frame[["open", "high", "low", "close", "volume"]]

    @classmethod
    def _candles_to_dataframe(
        cls,
        candles: list[Candle],
    ) -> pd.DataFrame:
        if not candles:
            return cls._validate_dataframe(pd.DataFrame())

        rows = [candle.to_dict() for candle in candles]
        frame = pd.DataFrame(rows)
        frame["timestamp"] = pd.to_datetime(
            frame["timestamp"],
            utc=True,
            errors="coerce",
        )
        frame = frame.set_index("timestamp")

        return cls._validate_dataframe(frame)

    # ------------------------------------------------------------------
    # Canonical API
    # ------------------------------------------------------------------

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> pd.DataFrame:
        """Fetch canonical candles through ProviderManager and quality-gate them."""
        normalized_symbol, normalized_timeframe, normalized_limit = (
            self._validate_request(symbol, timeframe, limit)
        )

        candles = await self.provider_manager.get_candles(
            symbol=normalized_symbol,
            timeframe=normalized_timeframe,
            limit=normalized_limit,
        )

        validated = self._validate_candles(
            candles,
            expected_symbol=normalized_symbol,
        )
        return self._candles_to_dataframe(validated)

    async def get_candles_list(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> list[Candle]:
        """Return quality-gated canonical Candle objects."""
        normalized_symbol, normalized_timeframe, normalized_limit = (
            self._validate_request(symbol, timeframe, limit)
        )

        candles = await self.provider_manager.get_candles(
            symbol=normalized_symbol,
            timeframe=normalized_timeframe,
            limit=normalized_limit,
        )

        return self._validate_candles(
            candles,
            expected_symbol=normalized_symbol,
        )

    # ------------------------------------------------------------------
    # Backwards-compatible provider-specific methods
    # ------------------------------------------------------------------

    async def get_finnhub_candles(
        self,
        symbol: str,
        resolution: str,
        from_timestamp: int,
        to_timestamp: int,
    ) -> pd.DataFrame:
        """Compatibility adapter for the previous Finnhub API."""
        if not isinstance(from_timestamp, int):
            raise TypeError("from_timestamp must be an integer.")
        if not isinstance(to_timestamp, int):
            raise TypeError("to_timestamp must be an integer.")
        if from_timestamp > to_timestamp:
            raise ValueError("from_timestamp cannot exceed to_timestamp.")

        normalized_symbol, normalized_timeframe, _ = self._validate_request(
            symbol,
            resolution,
            1,
        )

        candles = await self.provider_manager.get_candles(
            symbol=normalized_symbol,
            timeframe=normalized_timeframe,
            limit=5000,
        )

        validated = self._validate_candles(
            candles,
            expected_symbol=normalized_symbol,
        )

        start = datetime.fromtimestamp(from_timestamp, tz=timezone.utc)
        end = datetime.fromtimestamp(to_timestamp, tz=timezone.utc)

        filtered = [
            candle
            for candle in validated
            if start <= candle.timestamp <= end
        ]

        return self._candles_to_dataframe(filtered)

    async def get_oanda_candles(
        self,
        instrument: str,
        granularity: str = "M15",
        count: int = 500,
    ) -> pd.DataFrame:
        """Compatibility adapter for the previous OANDA API."""
        return await self.get_candles(
            symbol=instrument,
            timeframe=granularity,
            limit=count,
        )

    async def get_alphavantage_intraday(
        self,
        symbol: str,
        interval: str = "15min",
    ) -> pd.DataFrame:
        """Compatibility adapter for Alpha Vantage intraday requests."""
        interval_map = {
            "1min": "M1",
            "5min": "M5",
            "15min": "M15",
            "30min": "M30",
            "60min": "H1",
        }

        normalized = interval.strip().lower()
        timeframe = interval_map.get(normalized)

        if timeframe is None:
            raise ValueError(
                f"Unsupported Alpha Vantage interval: {interval!r}"
            )

        return await self.get_candles(
            symbol=symbol,
            timeframe=timeframe,
            limit=500,
        )

    async def get_latest_oanda_price(
        self,
        instrument: str,
    ) -> Optional[dict[str, Any]]:
        """
        Backwards-compatible latest OANDA price helper.

        Price snapshots are not part of the Candle contract, so this
        narrow operation remains delegated to the OANDA client's
        specialized endpoint. Candle retrieval never uses it.
        """
        if not isinstance(instrument, str):
            raise TypeError("instrument must be a string.")
        if not instrument.strip():
            raise ValueError("instrument cannot be empty.")

        if self._oanda_provider is None:
            self._oanda_provider = ProviderFactory.create("oanda")

        client = getattr(self._oanda_provider, "client", None)
        if client is None or not hasattr(client, "get_price"):
            raise RuntimeError(
                "OANDA provider does not expose the price endpoint."
            )

        data = await client.get_price(instrument.strip().upper())
        prices = data.get("prices", [])

        if not prices:
            return None

        return prices[0]


__all__ = ["MarketDataEngine"]
