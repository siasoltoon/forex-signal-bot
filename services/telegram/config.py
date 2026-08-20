from __future__ import annotations

from config.settings import Settings


class TelegramConfig:
    """
    Telegram configuration.
    """


    @property
    def token(self) -> str | None:

        return Settings.load().telegram_token


    @property
    def enabled(self) -> bool:

        return bool(
            self.token
        )
