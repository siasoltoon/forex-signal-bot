from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import pytest

from data.market_data import MarketDataEngine
from data.models import Candle


class FakeProviderManager:
    def __init__(self, candles: list[Candle]) -> None:
        self.candles = candles
        self.calls: list[dict[str, object]] = []

    async def get_candles(
        self,
        *,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> list[Candle]:
        self.calls.append(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "limit": limit,
            }
        )
        return list(self.candles)


def candle(
    *,
    symbol: str = "EUR_USD",
    minute: int = 0,
) -> Candle:
    return Candle(
        symbol=symbol,
        timestamp=datetime(
            2026,
            1,
            1,
            12,
            minute,
            tzinfo=timezone.utc,
        ),
        open=1.10,
        high=1.12,
        low=1.09,
        close=1.11,
        volume=100,
    )


@pytest.mark.asyncio
async def test_market_data_quality_gate_accepts_valid_candles() -> None:
    manager = FakeProviderManager([candle(minute=0), candle(minute=1)])
    engine = MarketDataEngine(manager)

    result = await engine.get_candles_list(
        symbol=" eur_usd ",
        timeframe=" m15 ",
        limit=10,
    )

    assert result == manager.candles
    assert manager.calls == [
        {
            "symbol": "EUR_USD",
            "timeframe": "M15",
            "limit": 10,
        }
    ]


@pytest.mark.asyncio
async def test_market_data_quality_gate_rejects_symbol_mismatch() -> None:
    manager = FakeProviderManager([candle(symbol="GBP_USD")])
    engine = MarketDataEngine(manager)

    with pytest.raises(ValueError, match="unexpected symbol"):
        await engine.get_candles_list(
            symbol="EUR_USD",
            timeframe="M15",
            limit=10,
        )


@pytest.mark.asyncio
async def test_market_data_quality_gate_runs_before_dataframe_conversion() -> None:
    manager = FakeProviderManager([candle(minute=0)])
    engine = MarketDataEngine(manager)

    result = await engine.get_candles(
        symbol="EUR_USD",
        timeframe="M15",
        limit=10,
    )

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]
    assert len(result) == 1
    assert result.index.tz is not None
