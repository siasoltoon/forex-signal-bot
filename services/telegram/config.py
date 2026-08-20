from __future__ import annotations

from config.settings import settings


class TelegramConfig:
    """
    Telegram configuration.
    """


    @property
    def token(self) -> str | None:
        return settings.telegram_token


    @property
    def enabled(self) -> bool:
        return bool(
            self.token
        )
