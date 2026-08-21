from __future__ import annotations

from dataclasses import dataclass

from config.environment import get_env


@dataclass(frozen=True)
class Settings:
    """
    Global application settings.
    """

    app_name: str = "forex-signal-bot"

    # Telegram
    telegram_token: str | None = None

    # Market data providers
    OANDA_API_KEY: str | None = None
    FINNHUB_API_KEY: str | None = None
    ALPHAVANTAGE_API_KEY: str | None = None


    @classmethod
    def load(cls) -> "Settings":
        """
        Load settings from environment variables.
        """

        return cls(
            telegram_token=get_env(
                "TELEGRAM_BOT_TOKEN"
            ),

            OANDA_API_KEY=get_env(
                "OANDA_API_KEY"
            ),

            FINNHUB_API_KEY=get_env(
                "FINNHUB_API_KEY"
            ),

            ALPHAVANTAGE_API_KEY=get_env(
                "ALPHAVANTAGE_API_KEY"
            ),
        )


settings = Settings.load()
