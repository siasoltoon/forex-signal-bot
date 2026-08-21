from __future__ import annotations

import pytest

from core.errors import ApplicationError

from data.factory import ProviderFactory

from data.providers.oanda_provider import OandaProvider
from data.providers.finnhub_provider import FinnhubProvider
from data.providers.alphavantage_provider import AlphaVantageProvider



def test_available_providers():

    providers = ProviderFactory.available()

    assert "oanda" in providers
    assert "finnhub" in providers
    assert "alphavantage" in providers



def test_create_oanda():

    provider = ProviderFactory.create(
        "oanda"
    )

    assert isinstance(
        provider,
        OandaProvider,
    )



def test_create_finnhub():

    provider = ProviderFactory.create(
        "finnhub"
    )

    assert isinstance(
        provider,
        FinnhubProvider,
    )



def test_create_alphavantage():

    provider = ProviderFactory.create(
        "alphavantage"
    )

    assert isinstance(
        provider,
        AlphaVantageProvider,
    )



def test_unknown_provider():

    with pytest.raises(
        ApplicationError
    ):
        ProviderFactory.create(
            "unknown"
        )
