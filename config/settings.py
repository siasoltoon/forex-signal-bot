from __future__ import annotations

from dataclasses import dataclass

from config.environment import get_env


@dataclass(frozen=True)
class Settings:
    """
    Global application settings.
    """

    app_name: str = "forex-signal-bot"

    telegram_token: str | None = None


    @classmethod
    def load(cls) -> "Settings":

        return cls(
            telegram_token=get_env(
                "TELEGRAM_BOT_TOKEN"
            ),
        )


settings = Settings.load()
