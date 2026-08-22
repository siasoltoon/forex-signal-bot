from __future__ import annotations
from datetime import datetime, timezone
import pytest
from core.errors import ApplicationError
from data.models import Candle
from data.provider_manager import ProviderManager

def candle(ts: int) -> Candle:
    return Candle(symbol='EUR_USD', timestamp=datetime.fromtimestamp(ts, tz=timezone.utc), open=1.1, high=1.11, low=1.09, close=1.105, volume=100.0)

class FakeProvider:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
    async def get_candles(self, symbol, timeframe, limit):
        self.calls.append((symbol, timeframe, limit))
        response = self.responses.pop(0)
        if isinstance(response, Exception): raise response
        return response

@pytest.mark.asyncio
async def test_explicit_provider_delegates_only_to_selected_provider():
    selected = FakeProvider([[candle(1), candle(2)]])
    other = FakeProvider([[candle(3)]])
    manager = ProviderManager(providers=[selected, other], retries=0)
    result = await manager.get_candles_explicit(manager.providers[0], 'eur_usd', 'm15', 2)
    assert result == [candle(1), candle(2)]
    assert selected.calls == [('EUR_USD', 'M15', 2)]
    assert other.calls == []

@pytest.mark.asyncio
async def test_explicit_provider_does_not_fallback_after_failure():
    selected = FakeProvider([RuntimeError('selected failed')])
    other = FakeProvider([[candle(2)]])
    manager = ProviderManager(providers=[selected, other], retries=0)
    with pytest.raises(ApplicationError) as exc_info:
        await manager.get_candles_explicit(manager.providers[0], 'EUR_USD', 'M15', 1)
    assert selected.calls == [('EUR_USD', 'M15', 1)]
    assert other.calls == []
    assert exc_info.value.__cause__ is not None

@pytest.mark.asyncio
async def test_explicit_provider_retries_selected_provider_only():
    selected = FakeProvider([RuntimeError('temporary'), [candle(1)]])
    other = FakeProvider([[candle(2)]])
    manager = ProviderManager(providers=[selected, other], retries=1, retry_delay=0)
    result = await manager.get_candles_explicit(manager.providers[0], 'EUR_USD', 'M15', 1)
    assert result == [candle(1)]
    assert len(selected.calls) == 2
    assert other.calls == []

@pytest.mark.asyncio
async def test_explicit_provider_rejects_unconfigured_provider():
    selected = FakeProvider([[candle(1)]])
    manager = ProviderManager(providers=[selected], retries=0)
    with pytest.raises(ApplicationError, match='not configured'):
        await manager.get_candles_explicit('oanda', 'EUR_USD', 'M15', 1)
    assert selected.calls == []
