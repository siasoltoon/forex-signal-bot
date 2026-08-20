from services.telegram.config import TelegramConfig


def test_telegram_disabled_without_token(
    monkeypatch,
):

    monkeypatch.delenv(
        "TELEGRAM_BOT_TOKEN",
        raising=False,
    )

    config = TelegramConfig()

    assert config.enabled is False
