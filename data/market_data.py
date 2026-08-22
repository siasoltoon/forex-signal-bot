from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional

import pandas as pd

from data.base import MarketDataProvider
from data.factory import ProviderFactory
from data.freshness import FreshnessPolicy, FreshnessReport
from data.models import Candle
from data.provider_manager import ProviderManager
from data.quality import DataQuality


logger = logging.getLogger(__name__)


class MarketDataEngine:
    """Unified application-facing market-data facade."""

    # Canonical project notation is unit-first (M15/H1/D1/W1).
    # Numeric-first notation (15m/1h/1d/1w) is also accepted because
    # providers and legacy callers may still use it.
    _TIMEFRAME_PATTERN = re.compile(
        r"^(?:(?P<unit_first>[mhdw])(?P<value_first>\d+)|(?P<value>\d+)(?P<unit>[mhdw]))$",
        re.IGNORECASE,
    )

    def __init__(
        self,
        provider_manager: ProviderManager | None = None,
        *,
        freshness_policy: type[FreshnessPolicy] = FreshnessPolicy,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.provider_manager = (
            provider_manager
            if provider_manager is not None
            else ProviderManager()
        )
        self.freshness_policy = freshness_policy
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._oanda_provider: Any | None = None

    @staticmethod
    def _validate_request(
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> tuple[str, str, int]:
        """Normalize requests through the canonical provider contract."""
        MarketDataProvider.validate_request(symbol, timeframe, limit)
        return (
            MarketDataProvider.normalize_symbol(symbol),
            MarketDataProvider.normalize_timeframe(timeframe),
            limit,
        )

    @staticmethod
    def _timeframe_to_timedelta(timeframe: str) -> timedelta:
        """Convert canonical or legacy timeframe notation to a duration."""
        if not isinstance(timeframe, str):
            raise TypeError("timeframe must be a string.")

        normalized = MarketDataProvider.normalize_timeframe(timeframe)
        match = MarketDataEngine._TIMEFRAME_PATTERN.fullmatch(normalized.strip())
        if match is None:
            raise ValueError(f"Unsupported timeframe: {timeframe!r}")

        if match.group("unit_first") is not None:
            unit = match.group("unit_first").lower()
            value = int(match.group("value_first"))
        else:
            unit = match.group("unit").lower()
            value = int(match.group("value"))

        if value < 1:
            raise ValueError(f"Unsupported timeframe: {timeframe!r}")

        multiplier = {
            "m": timedelta(minutes=1),
            "h": timedelta(hours=1),
            "d": timedelta(days=1),
            "w": timedelta(weeks=1),
        }[unit]
        return multiplier * value

    def _validate_freshness(
        self,
        candles: list[Candle],
        *,
        timeframe: str,
    ) -> FreshnessReport | None:
        """Apply the final freshness gate to the latest validated candle."""
        if not candles:
            return None

        now = self._clock()
        if not isinstance(now, datetime):
            raise TypeError("clock must return a datetime.")

        report = self.freshness_policy.assess(
            candles[-1].timestamp,
            now=now,
            timeframe=self._timeframe_to_timedelta(timeframe),
        )

        if report.status == FreshnessPolicy.WARNING:
            logger.warning(
                "Market data freshness warning: timeframe=%s age=%s",
                timeframe,
                report.age,
            )
        elif not report.is_usable:
            raise ValueError(
                "Market data is not fresh enough: "
                f"status={report.status}, age={report.age}, timeframe={timeframe}"
            )

        return report

    @staticmethod
    def _validate_candles(
        candles: list[Candle],
        *,
        expected_symbol: str,
    ) -> list[Candle]:
        """Apply the final deterministic data-quality gate."""
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
        """Validate and normalize an OHLCV DataFrame."""
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
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

        frame = frame.dropna(subset=[*required, "volume"])
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
    def _candles_to_dataframe(cls, candles: list[Candle]) -> pd.DataFrame:
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

    async def _get_quality_gated_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> list[Candle]:
        candles = await self.provider_manager.get_candles(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )
        validated = self._validate_candles(
            candles,
            expected_symbol=symbol,
        )
        self._validate_freshness(validated, timeframe=timeframe)
        return validated

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> pd.DataFrame:
        """Fetch canonical candles through ProviderManager."""
        normalized_symbol, normalized_timeframe, normalized_limit = (
            self._validate_request(symbol, timeframe, limit)
        )

        validated = await self._get_quality_gated_candles(
            normalized_symbol,
            normalized_timeframe,
            normalized_limit,
        )
        return self._candles_to_dataframe(validated)

    async def get_candles_list(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> list[Candle]:
        """Return quality- and freshness-gated canonical Candle objects."""
        normalized_symbol, normalized_timeframe, normalized_limit = (
            self._validate_request(symbol, timeframe, limit)
        )
        return await self._get_quality_gated_candles(
            normalized_symbol,
            normalized_timeframe,
            normalized_limit,
        )

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

        validated = await self._get_quality_gated_candles(
            normalized_symbol,
            normalized_timeframe,
            5000,
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
        """Return the latest OANDA price snapshot."""
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
