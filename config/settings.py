import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """
    Central application configuration.

    All sensitive values are loaded from environment variables.
    """

    BOT_TOKEN: str

    FINNHUB_API_KEY: str = ""
    ALPHAVANTAGE_API_KEY: str = ""
    OANDA_API_KEY: str = ""

    DATABASE_URL: str = ""
    REDIS_URL: str = ""

    AI_API_KEY: str = ""

    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "production"


def load_settings() -> Settings:
    bot_token = os.getenv("BOT_TOKEN", "").strip()

    if not bot_token:
        raise RuntimeError(
            "BOT_TOKEN environment variable is not configured."
        )

    return Settings(
        BOT_TOKEN=bot_token,
        FINNHUB_API_KEY=os.getenv("FINNHUB_API_KEY", "").strip(),
        ALPHAVANTAGE_API_KEY=os.getenv(
            "ALPHAVANTAGE_API_KEY", ""
        ).strip(),
        OANDA_API_KEY=os.getenv("OANDA_API_KEY", "").strip(),
        DATABASE_URL=os.getenv("DATABASE_URL", "").strip(),
        REDIS_URL=os.getenv("REDIS_URL", "").strip(),
        AI_API_KEY=os.getenv("AI_API_KEY", "").strip(),
        LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO").strip(),
        ENVIRONMENT=os.getenv(
            "ENVIRONMENT",
            "production",
        ).strip(),
    )


settings = load_settings()
