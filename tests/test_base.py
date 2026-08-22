from datetime import datetime, timezone

import pytest

from data.base import MarketDataProvider
from data.models import Candle


class DummyProvider(MarketDataProvider):
    name = "dummy"

    async def get_candles(self, symbol, timeframe, limit=MarketDataProvider.DEFAULT_LIMIT):
        self.validate_request(symbol, timeframe, limit)
        return []


def make_candle(second: int, symbol: str = "EUR_USD") -> Candle:
    return Candle(
        symbol=symbol,
        timestamp=datetime.fromtimestamp(second, tz=timezone.utc),
        open=1.10,
        high=1.12,
        low=1.09,
        close=1.11,
        volume=100.0,
    )


def test_validate_request_accepts_valid_request():
    DummyProvider.validate_request(" EUR_USD ", " M15 ", 10)


@pytest.mark.parametrize("symbol", ["", "   ", None, 123])
def test_validate_request_rejects_invalid_symbol(symbol):
    with pytest.raises((TypeError, ValueError)):
        DummyProvider.validate_request(symbol, "M15", 10)


@pytest.mark.parametrize("timeframe", ["", "   ", None, 123])
def test_validate_request_rejects_invalid_timeframe(timeframe):
    with pytest.raises((TypeError, ValueError)):
        DummyProvider.validate_request("EUR_USD", timeframe, 10)


@pytest.mark.parametrize("limit", [0, -1, 5001, True, 1.5, "10"])
def test_validate_request_rejects_invalid_limit(limit):
    with pytest.raises((TypeError, ValueError)):
        DummyProvider.validate_request("EUR_USD", "M15", limit)


def test_normalize_symbol():
    assert DummyProvider.normalize_symbol(" eur_usd ") == "EUR_USD"


@pytest.mark.parametrize("symbol", [None, 123, "   "])
def test_normalize_symbol_rejects_invalid_value(symbol):
    with pytest.raises((TypeError, ValueError)):
        DummyProvider.normalize_symbol(symbol)


def test_validate_candles_accepts_valid_sorted_data():
    candles = [make_candle(1), make_candle(2)]
    result = DummyProvider.validate_candles(candles, expected_symbol="eur_usd")
    assert result == candles
    assert result is not candles


def test_validate_candles_rejects_none_and_invalid_items():
    with pytest.raises(ValueError):
        DummyProvider.validate_candles(None)
    with pytest.raises(TypeError):
        DummyProvider.validate_candles(["invalid"])


def test_validate_candles_rejects_symbol_mismatch():
    with pytest.raises(ValueError):
        DummyProvider.validate_candles(
            [make_candle(1, "GBP_USD")],
            expected_symbol="EUR_USD",
        )


def test_validate_candles_rejects_duplicates_and_unsorted_data():
    with pytest.raises(ValueError):
        DummyProvider.validate_candles([make_candle(1), make_candle(1)])
    with pytest.raises(ValueError):
        DummyProvider.validate_candles([make_candle(2), make_candle(1)])


def test_normalize_candles_sorts_and_deduplicates():
    candles = [make_candle(3), make_candle(1), make_candle(2), make_candle(2)]
    result = DummyProvider.normalize_candles(candles)
    assert [c.timestamp for c in result] == [
        make_candle(1).timestamp,
        make_candle(2).timestamp,
        make_candle(3).timestamp,
    ]


def test_normalize_candles_can_keep_duplicates():
    candles = [make_candle(2), make_candle(1), make_candle(2)]
    result = DummyProvider.normalize_candles(candles, deduplicate=False)
    assert len(result) == 3
    assert result[0].timestamp < result[1].timestamp


def test_apply_limit_keeps_newest_candles():
    candles = [make_candle(1), make_candle(2), make_candle(3)]
    assert DummyProvider.apply_limit(candles, 2) == candles[-2:]
    assert DummyProvider.apply_limit(candles, 10) == candles


def test_normalize_timeframe():
    assert DummyProvider.normalize_timeframe(" 15m ") == "M15"
    assert DummyProvider.normalize_timeframe("1h") == "H1"
    assert DummyProvider.normalize_timeframe("1day") == "D1"


def test_default_configuration_is_true():
    assert DummyProvider().is_configured() is True


def test_provider_representation():
    provider = DummyProvider()
    assert "DummyProvider" in repr(provider)
    assert "dummy" in repr(provider)
