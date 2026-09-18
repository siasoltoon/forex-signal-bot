from datetime import datetime, timedelta, timezone

import pytest

from data.contracts import Candle, DataQuality, Market, MarketDataRequest, MarketDataResult
from data.failover import ProviderRouter, ProviderUnavailable
from data.provider import DataProvider
from data.validator import validate_candles


class StubProvider(DataProvider):
    def __init__(self, name: str, result: MarketDataResult | None = None, fail: bool = False) -> None:
        self.name = name
        self.result = result
        self.fail = fail

    def fetch(self, request: MarketDataRequest) -> MarketDataResult:
        if self.fail:
            raise RuntimeError("offline")
        assert self.result is not None
        return self.result


def test_validator_rejects_duplicate_and_bad_ohlc() -> None:
    now = datetime.now(timezone.utc)
    candles = (Candle(now, 10, 9, 8, 9), Candle(now, 9, 10, 8, 9))
    quality = validate_candles(candles)
    assert quality.valid is False
    assert quality.duplicates == 1
    assert quality.outliers == 1


def test_validator_detects_gap() -> None:
    now = datetime.now(timezone.utc)
    candles = (Candle(now, 1, 2, 0, 1), Candle(now + timedelta(minutes=3), 1, 2, 0, 1))
    quality = validate_candles(candles, expected_seconds=60)
    assert quality.gaps == 2


def test_router_fails_over() -> None:
    request = MarketDataRequest(Market.FOREX, "EURUSD", "1m")
    now = datetime.now(timezone.utc)
    result = MarketDataResult(request, (Candle(now, 1, 2, 0, 1),), "backup", DataQuality(True, 1.0))
    router = ProviderRouter((StubProvider("primary", fail=True), StubProvider("backup", result=result)))
    assert router.fetch(request).provider == "backup"


def test_router_raises_when_all_fail() -> None:
    request = MarketDataRequest(Market.FOREX, "EURUSD", "1m")
    router = ProviderRouter((StubProvider("primary", fail=True),))
    with pytest.raises(ProviderUnavailable):
        router.fetch(request)
