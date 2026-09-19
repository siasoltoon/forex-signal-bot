from datetime import datetime, timezone

import pytest

from data.models import Candle
from data.providers.binance_provider import BinanceProvider
from data.provider_manager import ProviderManager


class FakeBinance:
    def __init__(self):
        self.calls = []

    async def get_klines(self, symbol, interval, limit):
        self.calls.append((symbol, interval, limit))
        return [
            [1700000000000, "50000", "50100", "49900", "50050", "12.5", 1700000899999, "625625", 100, "6", "300000", "0"],
            [1700000900000, "50050", "50200", "50000", "50150", "10.0", 1700001799999, "501500", 90, "5", "250000", "0"],
        ]


@pytest.mark.asyncio
async def test_binance_provider_maps_btcusdt_to_spot_klines():
    client = FakeBinance()
    result = await BinanceProvider(client=client).get_candles("BTCUSDT", "M15", 10)

    assert len(result) == 2
    assert all(isinstance(candle, Candle) for candle in result)
    assert result[0].symbol == "BTCUSDT"
    assert result[0].close == 50050
    assert client.calls == [("BTCUSDT", "15m", 10)]


def test_binance_provider_declares_only_crypto_capability():
    provider = BinanceProvider(client=FakeBinance())
    assert provider.supports_symbol("BTCUSDT") is True
    assert provider.supports_symbol("EURUSD") is False
    assert provider.supports_symbol("AAPL") is False


@pytest.mark.asyncio
async def test_provider_manager_skips_non_capable_providers_for_crypto():
    class UnsupportedProvider:
        name = "fx_only"

        def __init__(self):
            self.calls = 0

        def supports_symbol(self, symbol):
            return False

        async def get_candles(self, symbol, timeframe, limit):
            self.calls += 1
            raise AssertionError("unsupported provider must be skipped")

    class CryptoProvider:
        name = "crypto"

        def supports_symbol(self, symbol):
            return True

        async def get_candles(self, symbol, timeframe, limit):
            return [
                Candle(
                    symbol=symbol,
                    timestamp=datetime(2026, 9, 19, 15, 0, tzinfo=timezone.utc),
                    open=50000,
                    high=50100,
                    low=49900,
                    close=50050,
                    volume=1,
                )
            ]

    unsupported = UnsupportedProvider()
    manager = ProviderManager(
        providers=[unsupported, CryptoProvider()],
        retries=0,
        cooldown_seconds=0,
    )

    result = await manager.get_candles("BTCUSDT", "M15", 10)

    assert len(result) == 1
    assert result[0].symbol == "BTCUSDT"
    assert unsupported.calls == 0
    assert any(
        failure.provider == "fx_only"
        and failure.error_type == "UnsupportedSymbol"
        and failure.attempt == 0
        for failure in manager.last_failures
    )
