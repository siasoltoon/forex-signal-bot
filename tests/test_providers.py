from __future__ import annotations
from datetime import datetime, timezone
import pytest
from data.models import Candle
from data.providers.oanda_provider import OandaProvider
from data.providers.finnhub_provider import FinnhubProvider
from data.providers.alphavantage_provider import AlphaVantageProvider

def test_oanda_provider_name(): assert OandaProvider().name == "oanda"
def test_finnhub_provider_name(): assert FinnhubProvider().name == "finnhub"
def test_alphavantage_provider_name(): assert AlphaVantageProvider().name == "alphavantage"

@pytest.mark.asyncio
async def test_oanda_provider_converts_candles(monkeypatch):
    provider = OandaProvider()
    async def fake_get_candles(instrument, granularity, count):
        return {"candles":[{"complete":True,"time":"2026-01-01T12:00:00Z","mid":{"o":"1.1000","h":"1.1200","l":"1.0900","c":"1.1100"},"volume":100}]}
    monkeypatch.setattr(provider.client,"get_candles",fake_get_candles)
    candles = await provider.get_candles("EUR_USD","M15",10)
    assert len(candles)==1 and isinstance(candles[0],Candle) and candles[0].symbol=="EUR_USD" and candles[0].close==1.11

@pytest.mark.asyncio
async def test_oanda_provider_skips_incomplete_candles(monkeypatch):
    provider=OandaProvider()
    async def fake_get_candles(instrument,granularity,count): return {"candles":[{"complete":False,"time":"2026-01-01T12:00:00Z","mid":{"o":"1","h":"1","l":"1","c":"1"}}]}
    monkeypatch.setattr(provider.client,"get_candles",fake_get_candles)
    assert await provider.get_candles("EUR_USD","M15")==[]

@pytest.mark.asyncio
async def test_finnhub_provider_converts_response(monkeypatch):
    provider=FinnhubProvider()
    async def fake_get_candles(symbol,resolution,from_timestamp,to_timestamp):
        return {"s":"ok","t":[1767268800],"o":[1.10],"h":[1.12],"l":[1.09],"c":[1.11],"v":[100]}
    monkeypatch.setattr(provider.client,"get_candles",fake_get_candles)
    candles=await provider.get_candles("EUR_USD","M15",10)
    assert len(candles)==1 and candles[0].close==1.11

@pytest.mark.asyncio
async def test_alphavantage_provider_converts_response(monkeypatch):
    provider=AlphaVantageProvider()
    async def fake_get_forex_intraday(from_currency,to_currency,interval):
        return {"Time Series FX (15min)":{"2026-01-01 12:00:00":{"1. open":"1.1000","2. high":"1.1200","3. low":"1.0900","4. close":"1.1100","5. volume":"100"}}}
    monkeypatch.setattr(provider.client,"get_forex_intraday",fake_get_forex_intraday)
    candles=await provider.get_candles("EUR_USD","M15",10)
    assert len(candles)==1 and candles[0].close==1.11

@pytest.mark.asyncio
async def test_provider_invalid_symbol():
    provider=OandaProvider()
    with pytest.raises(ValueError): await provider.get_candles("","M15")
