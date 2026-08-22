from datetime import datetime, timezone

import pytest

from core.errors import ApplicationError
from data.models import Candle
from data.providers.finnhub_provider import FinnhubProvider


class FakeClient:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    async def get_candles(self, symbol, resolution, from_timestamp, to_timestamp):
        self.calls.append((symbol, resolution, from_timestamp, to_timestamp))
        if self.error is not None:
            raise self.error
        return self.result


def response(ts, *, status="ok", opens=None, highs=None, lows=None, closes=None, volumes=None):
    return {
        "s": status,
        "t": ts,
        "o": opens if opens is not None else [1.10 for _ in ts],
        "h": highs if highs is not None else [1.12 for _ in ts],
        "l": lows if lows is not None else [1.09 for _ in ts],
        "c": closes if closes is not None else [1.11 for _ in ts],
        "v": volumes if volumes is not None else [100.0 for _ in ts],
    }


@pytest.mark.asyncio
async def test_get_candles_forwards_normalized_request():
    client = FakeClient(result=response([1_700_000_000]))
    provider = FinnhubProvider(client=client)

    result = await provider.get_candles(" eur_usd ", "M15", limit=10)

    assert len(result) == 1
    assert client.calls[0][0] == "EUR_USD"
    assert client.calls[0][1] == "15"
    assert client.calls[0][3] > client.calls[0][2]


@pytest.mark.asyncio
async def test_get_candles_maps_finnhub_response_to_candle():
    ts = [1_700_000_000]
    client = FakeClient(result=response(ts))
    provider = FinnhubProvider(client=client)

    result = await provider.get_candles("EUR_USD", "M15", 10)

    assert len(result) == 1
    assert isinstance(result[0], Candle)
    assert result[0].symbol == "EUR_USD"
    assert result[0].timestamp == datetime.fromtimestamp(ts[0], tz=timezone.utc)
    assert result[0].open == 1.10
    assert result[0].high == 1.12
    assert result[0].low == 1.09
    assert result[0].close == 1.11
    assert result[0].volume == 100.0


@pytest.mark.asyncio
async def test_get_candles_supports_hour_resolution():
    client = FakeClient(result=response([1_700_000_000]))
    provider = FinnhubProvider(client=client)

    await provider.get_candles("EUR_USD", "H1", 10)

    assert client.calls[0][1] == "60"


@pytest.mark.asyncio
async def test_get_candles_rejects_invalid_response_status():
    client = FakeClient(result=response([1_700_000_000], status="no_data"))
    provider = FinnhubProvider(client=client)

    with pytest.raises((ValueError, ApplicationError)):
        await provider.get_candles("EUR_USD", "M15", 10)


@pytest.mark.asyncio
async def test_get_candles_rejects_mismatched_array_lengths():
    client = FakeClient(
        result=response(
            [1_700_000_000, 1_700_001_000],
            opens=[1.1],
        )
    )
    provider = FinnhubProvider(client=client)

    with pytest.raises((ValueError, ApplicationError)):
        await provider.get_candles("EUR_USD", "M15", 10)


@pytest.mark.asyncio
async def test_get_candles_wraps_client_errors():
    client = FakeClient(error=RuntimeError("finnhub unavailable"))
    provider = FinnhubProvider(client=client)

    with pytest.raises(ApplicationError):
        await provider.get_candles("EUR_USD", "M15", 10)


@pytest.mark.asyncio
async def test_get_candles_rejects_invalid_request_without_calling_client():
    client = FakeClient(result=response([1_700_000_000]))
    provider = FinnhubProvider(client=client)

    with pytest.raises((TypeError, ValueError, ApplicationError)):
        await provider.get_candles("", "M15", 10)

    assert client.calls == []
