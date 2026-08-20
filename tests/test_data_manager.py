import pytest

from data.base import MarketDataProvider
from data.manager import DataManager


class FakeProvider(
    MarketDataProvider
):
    name = "fake"

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ):
        return []


def test_register_provider():

    manager = DataManager()

    provider = FakeProvider()

    manager.register(
        provider
    )

    assert (
        manager.list_providers()
        == ["fake"]
    )


def test_duplicate_provider():

    manager = DataManager()

    manager.register(
        FakeProvider()
    )

    with pytest.raises(
        Exception
    ):
        manager.register(
            FakeProvider()
        )


def test_missing_provider():

    manager = DataManager()

    with pytest.raises(
        Exception
    ):
        manager.get_provider(
            "missing"
        )
