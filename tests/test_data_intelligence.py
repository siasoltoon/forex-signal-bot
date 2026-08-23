from datetime import datetime, timedelta, timezone

import pytest

from data.intelligence import DataIntelligence
from data.models import Candle


def candle(ts: datetime, close: float = 1.1) -> Candle:
    return Candle("EUR_USD", ts, close, close + 0.01, close - 0.01, close, 10.0)


def test_valid_data_crosses_intelligence_boundary() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    candles = [
        candle(now - timedelta(minutes=2)),
        candle(now - timedelta(minutes=1), 1.101),
    ]
    result = DataIntelligence().validate(
        candles,
        symbol="eur_usd",
        timeframe_interval=timedelta(minutes=1),
        now=now,
        source="oanda",
    )
    assert result.symbol == "EUR_USD"
    assert result.quality.usable
    assert result.source == "oanda"


def test_stale_data_is_rejected() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    candles = [candle(now - timedelta(minutes=10))]
    with pytest.raises(ValueError, match="stale|reject"):
        DataIntelligence().validate(
            candles,
            symbol="EUR_USD",
            timeframe_interval=timedelta(minutes=1),
            now=now,
            source="oanda",
        )


def test_provider_comparison_requires_common_timestamps() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    a = [candle(now, 1.1)]
    b = [candle(now, 1.1)]
    assert DataIntelligence.compare_provider_data(a, b)
    assert not DataIntelligence.compare_provider_data(a, [candle(now + timedelta(minutes=1), 1.1)])
