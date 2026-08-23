from core.production_readiness import ProductionReadiness


def test_paper_mode_does_not_fabricate_missing_credentials() -> None:
    result = ProductionReadiness({"DEBUG": "false"}).evaluate(live=False)
    assert result.ready
    assert any("market-data provider" in warning for warning in result.warnings)


def test_live_mode_requires_real_market_data() -> None:
    result = ProductionReadiness(
        {
            "DEBUG": "false",
            "TELEGRAM_BOT_TOKEN": "token",
            "LIVE_TRADING_ENABLED": "true",
            "PAPER_TRADING": "false",
        }
    ).evaluate(live=True)
    assert not result.ready
    assert any("market-data provider" in reason for reason in result.blocking_reasons)


def test_live_mode_requires_explicit_execution_enablement() -> None:
    result = ProductionReadiness(
        {
            "DEBUG": "false",
            "TELEGRAM_BOT_TOKEN": "token",
            "OANDA_API_KEY": "real-provider-key",
            "PAPER_TRADING": "false",
        }
    ).evaluate(live=True)
    assert not result.ready
    assert any("LIVE_TRADING_ENABLED" in reason for reason in result.blocking_reasons)


def test_live_mode_can_be_ready_only_with_explicit_real_configuration() -> None:
    result = ProductionReadiness(
        {
            "DEBUG": "false",
            "TELEGRAM_BOT_TOKEN": "token",
            "OANDA_API_KEY": "real-provider-key",
            "LIVE_TRADING_ENABLED": "true",
            "PAPER_TRADING": "false",
            "DEFAULT_SYMBOL": "EURUSD",
            "DEFAULT_TIMEFRAME": "1h",
        }
    ).evaluate(live=True)
    assert result.ready
    assert result.blocking_reasons == ()
