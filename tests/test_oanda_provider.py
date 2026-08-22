from datetime import datetime, timezone

import pytest

from core.errors import ApplicationError
from data.models import Candle
from data.providers.oanda_provider import OandaProvider


class FakeClient:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    async def get_candles(self, symbol, timeframe, limit):
        self.calls.append((symbol, timeframe, limit))
        if self.error is not None:
            raise self.error
        return self.result


def raw_candle(ts, *, complete=True, open="1.10", high="1.12", low="1.09", close="1.11", volume="100"):
    return {
        "time": ts,
        "complete": complete,
        "mid": {"o": open, "h": high, "l": low, "c": close},
        "volume": volume,
    }


@pytest.mark.asyncio
async def test_get_candles_forwards_normalized_request(monkeypatch):
    client = FakeClient(result=[])
    provider = OandaProvider(client=client)

    result = await provider.get_candles(" eur_usd ", "15m", limit=10)

    assert result == []
    assert client.calls == [("EUR_USD", "M15", 10)]


@pytest.mark.asyncio
async def test_get_candles_maps_valid_oanda_candles_to_candle(monkeypatch):
    client = FakeClient(result=[raw_candle("2026-01-01T00:00:00Z")])
    provider = OandaProvider(client=client)

    result = await provider.get_candles("EUR_USD", "M15", 10)

    assert len(result) == 1
    assert isinstance(result[0], Candle)
    assert result[0].symbol == "EUR_USD"
    assert result[0].timestamp.tzinfo == timezone.utc
    assert result[0].open == 1.10
    assert result[0].high == 1.12
    assert result[0].low == 1.09
    assert result[0].close == 1.11
    assert result[0].volume == 100.0


@pytest.mark.asyncio
async def test_get_candles_skips_incomplete_candles():
    client = FakeClient(
        result=[
            raw_candle("2026-01-01T00:00:00Z", complete=False),
            raw_candle("2026-01-01T00:15:00Z"),
        ]
    )
    provider = OandaProvider(client=client)

    result = await provider.get_candles("EUR_USD", "M15", 10)

    assert len(result) == 1
    assert result[0].timestamp == datetime(2026, 1, 1, 0, 15, tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_get_candles_deduplicates_and_sorts():
    candle_a = raw_candle("2026-01-01T00:00:00Z")
    candle_b = raw_candle("2026-01-01T00:15:00Z")
    client = FakeClient(result=[candle_b, candle_a, candle_b])
    provider = OandaProvider(client=client)

    result = await provider.get_candles("EUR_USD", "M15", 10)

    assert [c.timestamp for c in result] == [
        datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 1, 0, 15, tzinfo=timezone.utc),
    ]


@pytest.mark.asyncio
async def test_get_candles_applies_limit():
    client = FakeClient(
        result=[
            raw_candle("2026-01-01T00:00:00Z"),
            raw_candle("2026-01-01T00:15:00Z"),
            raw_candle("2026-01-01T00:30:00Z"),
        ]
    )
    provider = OandaProvider(client=client)

    result = await provider.get_candles("EUR_USD", "M15", 2)

    assert len(result) == 2
    assert result[-1].timestamp == datetime(2026, 1, 1, 0, 30, tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_get_candles_wraps_client_errors():
    client = FakeClient(error=RuntimeError("oanda unavailable"))
    provider = OandaProvider(client=client)

    with pytest.raises(ApplicationError):
        await provider.get_candles("EUR_USD", "M15", 10)


@pytest.mark.asyncio
async def test_get_candles_rejects_invalid_request():
    client = FakeClient(result=[])
    provider = OandaProvider(client=client)

    with pytest.raises((TypeError, ValueError, ApplicationError)):
        await provider.get_candles("", "M15", 10)

    assert client.calls == []
