from config.settings import Settings


def test_settings_without_token(
    monkeypatch,
):

    monkeypatch.delenv(
        "TELEGRAM_BOT_TOKEN",
        raising=False,
    )

    settings = Settings.load()

    assert settings.telegram_token is None
