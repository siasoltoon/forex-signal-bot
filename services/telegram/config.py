from __future__ import annotations

import os


class TelegramConfig:
    """
    Telegram bot configuration.
    """

    @property
    def token(self) -> str | None:
        return os.getenv(
            "TELEGRAM_BOT_TOKEN"
        )

    @property
    def enabled(self) -> bool:
        return bool(self.token)
