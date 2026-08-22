from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from core.errors import ApplicationError
from data.base import MarketDataProvider
from data.factory import ProviderFactory
from data.models import Candle
from data.providers.alphavantage_provider import AlphaVantageProvider
from data.providers.finnhub_provider import FinnhubProvider
from data.providers.oanda_provider import OandaProvider


class FakeProvider(MarketDataProvider):
    name = "fake"

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = MarketDataProvider.DEFAULT_LIMIT,
    ) -> list[Candle]:
        return []


class UnconfiguredProvider(FakeProvider):
    name = "unconfigured"

    def is_configured(self) -> bool:
        return False


@pytest.fixture(autouse=True)
def restore_factory_state():
    providers = dict(ProviderFactory._providers)
    aliases = dict(ProviderFactory._aliases)
    default_provider = ProviderFactory._default_provider

    yield

    ProviderFactory._providers.clear()
    ProviderFactory._providers.update(providers)
    ProviderFactory._aliases.clear()
    ProviderFactory._aliases.update(aliases)
    ProviderFactory._default_provider = default_provider


def test_available_providers():
    providers = ProviderFactory.available()

    assert "oanda" in providers
    assert "finnhub" in providers
    assert "alphavantage" in providers
    assert providers == sorted(providers)


def test_create_oanda():
    provider = ProviderFactory.create("oanda")

    assert isinstance(provider, OandaProvider)


def test_create_finnhub():
    provider = ProviderFactory.create("finnhub")

    assert isinstance(provider, FinnhubProvider)


def test_create_alphavantage():
    provider = ProviderFactory.create("alphavantage")

    assert isinstance(provider, AlphaVantageProvider)


def test_create_normalizes_provider_name_and_alias():
    assert isinstance(ProviderFactory.create(" OANDA "), OandaProvider)
    assert isinstance(ProviderFactory.create("FinnHub"), FinnhubProvider)
    assert isinstance(
        ProviderFactory.create(" Alpha-Vantage "),
        AlphaVantageProvider,
    )
    assert isinstance(
        ProviderFactory.create("alpha_vantage"),
        AlphaVantageProvider,
    )


def test_normalize_name_rejects_invalid_values():
    with pytest.raises(TypeError):
        ProviderFactory.normalize_name(None)  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        ProviderFactory.normalize_name("   ")


def test_unknown_provider():
    with pytest.raises(ApplicationError):
        ProviderFactory.create("unknown")


def test_default_provider_contract():
    assert ProviderFactory.default_name() == "oanda"
    assert isinstance(ProviderFactory.create_default(), OandaProvider)


def test_set_default_normalizes_name():
    ProviderFactory.register("fake", FakeProvider)

    ProviderFactory.set_default(" FAKE ")

    assert ProviderFactory.default_name() == "fake"
    assert isinstance(ProviderFactory.create_default(), FakeProvider)


def test_set_default_rejects_unregistered_provider():
    with pytest.raises(ApplicationError):
        ProviderFactory.set_default("missing")


def test_register_new_provider_and_create_it():
    ProviderFactory.register("my-provider", FakeProvider)

    assert ProviderFactory.is_supported("my-provider")
    assert isinstance(ProviderFactory.create("MY-PROVIDER"), FakeProvider)
    assert ProviderFactory.get_provider_class("my-provider") is FakeProvider


def test_register_rejects_duplicate_without_overwrite():
    with pytest.raises(ApplicationError):
        ProviderFactory.register("oanda", FakeProvider)


def test_register_allows_explicit_overwrite():
    ProviderFactory.register("oanda", FakeProvider, overwrite=True)

    assert ProviderFactory.get_provider_class("oanda") is FakeProvider
    assert isinstance(ProviderFactory.create("oanda"), FakeProvider)


def test_register_rejects_non_provider_class():
    class NotAProvider:
        pass

    with pytest.raises(TypeError):
        ProviderFactory.register("invalid", NotAProvider)  # type: ignore[arg-type]


def test_register_rejects_non_class_value():
    with pytest.raises(TypeError):
        ProviderFactory.register("invalid", object())  # type: ignore[arg-type]


def test_unregister_non_default_provider_and_remove_aliases():
    ProviderFactory.register("temporary", FakeProvider)
    ProviderFactory.set_default("temporary")
    ProviderFactory.set_default("oanda")

    ProviderFactory.unregister("temporary")

    assert not ProviderFactory.is_supported("temporary")
    with pytest.raises(ApplicationError):
        ProviderFactory.create("temporary")


def test_unregister_rejects_default_provider():
    with pytest.raises(ApplicationError):
        ProviderFactory.unregister("oanda")


def test_unregister_rejects_unknown_provider():
    with pytest.raises(ApplicationError):
        ProviderFactory.unregister("missing")


def test_is_supported_is_safe_for_invalid_input():
    assert ProviderFactory.is_supported(" OANDA ") is True
    assert ProviderFactory.is_supported("missing") is False
    assert ProviderFactory.is_supported(None) is False  # type: ignore[arg-type]
    assert ProviderFactory.is_supported("   ") is False


def test_registry_returns_snapshot():
    snapshot = ProviderFactory.registry()
    snapshot.clear()

    assert "oanda" in ProviderFactory.available()


def test_aliases_returns_snapshot():
    aliases = ProviderFactory.aliases()
    aliases.clear()

    assert ProviderFactory.normalize_name("alpha-vantage") == "alphavantage"


def test_configured_provider_uses_local_configuration_check():
    ProviderFactory.register("fake", FakeProvider)
    ProviderFactory.register("unconfigured", UnconfiguredProvider)

    assert ProviderFactory.configured("fake") is True
    assert ProviderFactory.configured("unconfigured") is False
    assert "fake" in ProviderFactory.configured_providers()
    assert "unconfigured" not in ProviderFactory.configured_providers()


def test_get_provider_class_rejects_unknown_provider():
    with pytest.raises(ApplicationError):
        ProviderFactory.get_provider_class("missing")
