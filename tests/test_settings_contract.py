from config.settings import Settings, get_bool_env, get_env, get_float_env, get_int_env, get_list_env, get_required_env


def test_get_env_strips_values_and_uses_default(monkeypatch):
    monkeypatch.setenv("TEST_ENV", "  value  ")
    assert get_env("TEST_ENV") == "value"
    monkeypatch.delenv("TEST_ENV")
    assert get_env("TEST_ENV", "fallback") == "fallback"


def test_get_required_env_rejects_missing_value(monkeypatch):
    monkeypatch.delenv("REQUIRED_ENV", raising=False)
    try:
        get_required_env("REQUIRED_ENV")
    except RuntimeError as error:
        assert str(error) == "Required environment variable 'REQUIRED_ENV' is not configured."
    else:
        raise AssertionError("missing required environment variable did not raise")


def test_typed_environment_parsers(monkeypatch):
    monkeypatch.setenv("BOOL_ENV", "yes")
    monkeypatch.setenv("INT_ENV", "42")
    monkeypatch.setenv("FLOAT_ENV", "1.25")
    monkeypatch.setenv("LIST_ENV", "EURUSD, GBPUSD, , XAUUSD")

    assert get_bool_env("BOOL_ENV") is True
    assert get_int_env("INT_ENV", 0) == 42
    assert get_float_env("FLOAT_ENV", 0.0) == 1.25
    assert get_list_env("LIST_ENV") == ["EURUSD", "GBPUSD", "XAUUSD"]


def test_settings_load_maps_environment_values(monkeypatch):
    monkeypatch.setenv("APP_NAME", "Test Bot")
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("RISK_PER_TRADE", "0.02")
    monkeypatch.setenv("MAX_OPEN_POSITIONS", "7")
    monkeypatch.setenv("AI_API_KEY", "ai-key")
    monkeypatch.setenv("AI_TEMPERATURE", "1.5")

    loaded = Settings.load()

    assert loaded.app_name == "Test Bot"
    assert loaded.environment == "testing"
    assert loaded.debug is True
    assert loaded.telegram_token == "token"
    assert loaded.telegram_enabled is True
    assert loaded.risk_per_trade == 0.02
    assert loaded.max_open_positions == 7
    assert loaded.ai_api_key == "ai-key"
    assert loaded.ai_enabled is True
    assert loaded.ai_temperature == 1.5


def test_settings_load_clamps_ai_temperature(monkeypatch):
    monkeypatch.setenv("AI_TEMPERATURE", "99")
    assert Settings.load().ai_temperature == 2.0

    monkeypatch.setenv("AI_TEMPERATURE", "-5")
    assert Settings.load().ai_temperature == 0.0
