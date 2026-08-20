from __future__ import annotations

import logging
from typing import Any, Optional

import pandas as pd

from data.alphavantage import AlphaVantageClient
from data.finnhub import FinnhubClient
from data.oanda import OandaClient


logger = logging.getLogger(__name__)


class MarketDataEngine:
    """
    Unified market-data layer.

    Analysis modules should communicate with this class
    instead of communicating directly with individual APIs.
    """

    def __init__(self) -> None:
        self.finnhub = FinnhubClient()
        self.alphavantage = AlphaVantageClient()
        self.oanda = OandaClient()

    @staticmethod
    def _validate_dataframe(
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Validate and normalize OHLCV data.
        """

        required_columns = [
            "open",
            "high",
            "low",
            "close",
        ]

        missing = [
            column
            for column in required_columns
            if column not in dataframe.columns
        ]

        if missing:
            raise ValueError(
                f"Missing OHLC columns: {missing}"
            )

        dataframe = dataframe.copy()

        for column in required_columns:
            dataframe[column] = pd.to_numeric(
                dataframe[column],
                errors="coerce",
            )

        if "volume" in dataframe.columns:
            dataframe["volume"] = pd.to_numeric(
                dataframe["volume"],
                errors="coerce",
            )
        else:
            dataframe["volume"] = 0.0

        dataframe = dataframe.dropna(
            subset=required_columns
        )

        dataframe = dataframe.sort_index()

        return dataframe

    @staticmethod
    def _finnhub_to_dataframe(
        data: dict[str, Any],
    ) -> pd.DataFrame:
        """
        Convert Finnhub candle response to DataFrame.
        """

        if not data:
            return pd.DataFrame()

        timestamps = data.get("t", [])

        dataframe = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(
                    timestamps,
                    unit="s",
                    utc=True,
                ),
                "open": data.get("o", []),
                "high": data.get("h", []),
                "low": data.get("l", []),
                "close": data.get("c", []),
                "volume": data.get("v", []),
            }
        )

        if dataframe.empty:
            return dataframe

        dataframe = dataframe.set_index(
            "timestamp"
        )

        return MarketDataEngine._validate_dataframe(
            dataframe
        )

    @staticmethod
    def _oanda_to_dataframe(
        data: dict[str, Any],
    ) -> pd.DataFrame:
        """
        Convert OANDA candle response to DataFrame.
        """

        candles = data.get("candles", [])

        rows = []

        for candle in candles:
            if not candle.get("complete", True):
                continue

            mid = candle.get("mid", {})

            rows.append(
                {
                    "timestamp": pd.to_datetime(
                        candle.get("time"),
                        utc=True,
                    ),
                    "open": mid.get("o"),
                    "high": mid.get("h"),
                    "low": mid.get("l"),
                    "close": mid.get("c"),
                    "volume": candle.get(
                        "volume",
                        0,
                    ),
                }
            )

        if not rows:
            return pd.DataFrame()

        dataframe = pd.DataFrame(rows)

        dataframe = dataframe.set_index(
            "timestamp"
        )

        return MarketDataEngine._validate_dataframe(
            dataframe
        )

    @staticmethod
    def _alphavantage_to_dataframe(
        data: dict[str, Any],
    ) -> pd.DataFrame:
        """
        Convert Alpha Vantage intraday response
        to DataFrame.
        """

        series_key = next(
            (
                key
                for key in data
                if key.startswith(
                    "Time Series"
                )
            ),
            None,
        )

        if not series_key:
            return pd.DataFrame()

        series = data[series_key]

        rows = []

        for timestamp, values in series.items():
            rows.append(
                {
                    "timestamp": pd.to_datetime(
                        timestamp,
                        utc=True,
                    ),
                    "open": values.get(
                        "1. open"
                    ),
                    "high": values.get(
                        "2. high"
                    ),
                    "low": values.get(
                        "3. low"
                    ),
                    "close": values.get(
                        "4. close"
                    ),
                    "volume": values.get(
                        "5. volume",
                        0,
                    ),
                }
            )

        if not rows:
            return pd.DataFrame()

        dataframe = pd.DataFrame(rows)

        dataframe = dataframe.set_index(
            "timestamp"
        )

        return MarketDataEngine._validate_dataframe(
            dataframe
        )

    async def get_finnhub_candles(
        self,
        symbol: str,
        resolution: str,
        from_timestamp: int,
        to_timestamp: int,
    ) -> pd.DataFrame:
        """
        Get normalized candle data from Finnhub.
        """

        data = await self.finnhub.get_candles(
            symbol=symbol,
            resolution=resolution,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
        )

        if not data:
            return pd.DataFrame()

        return self._finnhub_to_dataframe(data)

    async def get_oanda_candles(
        self,
        instrument: str,
        granularity: str = "M15",
        count: int = 500,
    ) -> pd.DataFrame:
        """
        Get normalized candle data from OANDA.
        """

        data = await self.oanda.get_candles(
            instrument=instrument,
            granularity=granularity,
            count=count,
        )

        return self._oanda_to_dataframe(data)

    async def get_alphavantage_intraday(
        self,
        symbol: str,
        interval: str = "15min",
    ) -> pd.DataFrame:
        """
        Get normalized intraday data from
        Alpha Vantage.
        """

        data = await self.alphavantage.get_intraday(
            symbol=symbol,
            interval=interval,
        )

        return self._alphavantage_to_dataframe(data)

    async def get_latest_oanda_price(
        self,
        instrument: str,
    ) -> Optional[dict[str, Any]]:
        """
        Get the latest OANDA price.
        """

        data = await self.oanda.get_price(
            instrument
        )

        prices = data.get("prices", [])

        if not prices:
            return None

        return prices[0]
