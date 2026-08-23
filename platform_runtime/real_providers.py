from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import httpx

from .data_runtime import Candle, MarketRequest, Provider


class HttpProviderBase:
    name = "http"

    def __init__(self, api_key: str | None = None, timeout: float = 15.0) -> None:
        self.api_key = api_key
        self.timeout = timeout

    async def health(self) -> bool:
        return bool(self.api_key)

    @staticmethod
    def _dt(value: str | int | float) -> datetime:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        text = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class TwelveDataProvider(HttpProviderBase):
    name = "twelvedata"

    async def fetch(self, request: MarketRequest) -> tuple[Candle, ...]:
        if not self.api_key:
            raise RuntimeError("TWELVEDATA_API_KEY is not configured")
        params = {"symbol": request.symbol, "interval": request.timeframe, "outputsize": request.limit, "apikey": self.api_key, "format": "JSON"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get("https://api.twelvedata.com/time_series", params=params)
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
        if payload.get("status") == "error":
            raise RuntimeError(str(payload.get("message", "TwelveData error")))
        values = payload.get("values") or []
        return tuple(Candle(self._dt(row["datetime"]), float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"]), float(row["volume"]) if row.get("volume") is not None else None) for row in reversed(values))


class AlphaVantageProvider(HttpProviderBase):
    name = "alphavantage"

    async def fetch(self, request: MarketRequest) -> tuple[Candle, ...]:
        if not self.api_key:
            raise RuntimeError("ALPHAVANTAGE_API_KEY is not configured")
        if request.market.value != "forex":
            raise ValueError("AlphaVantageProvider currently implements FX only")
        if ":" not in request.symbol:
            raise ValueError("AlphaVantage FX symbol must be FROM:TO")
        from_symbol, to_symbol = request.symbol.split(":", 1)
        function = "FX_INTRADAY"
        params = {"function": function, "from_symbol": from_symbol, "to_symbol": to_symbol, "interval": request.timeframe, "outputsize": "full", "apikey": self.api_key}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get("https://www.alphavantage.co/query", params=params)
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
        series_key = next((key for key in payload if key.startswith("Time Series FX")), None)
        if not series_key:
            raise RuntimeError(str(payload.get("Note") or payload.get("Information") or "AlphaVantage returned no time series"))
        rows = payload[series_key]
        candles = []
        for stamp, row in rows.items():
            candles.append(Candle(self._dt(stamp), float(row["1. open"]), float(row["2. high"]), float(row["3. low"]), float(row["4. close"])))
        return tuple(sorted(candles, key=lambda c: c.timestamp)[-request.limit:])


class OandaProvider(HttpProviderBase):
    name = "oanda"

    def __init__(self, api_key: str | None = None, account_environment: str | None = None, timeout: float = 15.0) -> None:
        super().__init__(api_key, timeout)
        self.base_url = "https://api-fxtrade.oanda.com" if (account_environment or os.getenv("OANDA_ENV", "practice")) == "live" else "https://api-fxpractice.oanda.com"

    async def fetch(self, request: MarketRequest) -> tuple[Candle, ...]:
        if not self.api_key:
            raise RuntimeError("OANDA_API_KEY is not configured")
        params = {"granularity": request.timeframe, "count": request.limit, "price": "M"}
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/v3/instruments/{request.symbol}/candles", params=params, headers=headers)
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
        candles = []
        for item in payload.get("candles", []):
            if not item.get("complete", True):
                continue
            mid = item.get("mid") or {}
            candles.append(Candle(self._dt(item["time"]), float(mid["o"]), float(mid["h"]), float(mid["l"]), float(mid["c"]), float(item["volume"])))
        return tuple(candles)


def configured_providers() -> tuple[Provider, ...]:
    return tuple(p for p in (
        OandaProvider(os.getenv("OANDA_API_KEY")),
        TwelveDataProvider(os.getenv("TWELVEDATA_API_KEY")),
        AlphaVantageProvider(os.getenv("ALPHAVANTAGE_API_KEY")),
    ) if p.api_key)
