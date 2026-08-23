from core.production_activation import assert_no_synthetic_mode, validate_activation


def test_activation_requires_real_market_and_telegram_credentials():
    status = validate_activation({})
    assert not status.ready
    assert "OANDA_API_KEY" in status.missing
    assert "TWELVEDATA_API_KEY" in status.missing
    assert "TELEGRAM_BOT_TOKEN" in status.missing


def test_paper_mode_can_be_ready_with_required_credentials():
    status = validate_activation({
        "OANDA_API_KEY": "configured",
        "TWELVEDATA_API_KEY": "configured",
        "TELEGRAM_BOT_TOKEN": "configured",
        "PAPER_TRADING": "true",
    })
    assert status.ready


def test_live_mode_requires_explicit_paper_off():
    status = validate_activation({
        "OANDA_API_KEY": "configured",
        "TWELVEDATA_API_KEY": "configured",
        "TELEGRAM_BOT_TOKEN": "configured",
        "LIVE_TRADING_ENABLED": "true",
        "PAPER_TRADING": "true",
    })
    assert not status.ready


def test_synthetic_market_data_is_rejected():
    try:
        assert_no_synthetic_mode({"ALLOW_SYNTHETIC_MARKET_DATA": "true"})
    except RuntimeError:
        return
    raise AssertionError("synthetic market data must be rejected")
