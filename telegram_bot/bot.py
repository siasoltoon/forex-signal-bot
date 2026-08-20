from __future__ import annotations

import os

from telegram.ext import (
    Application,
)


def get_bot_token() -> str:
    token = os.getenv(
        "TELEGRAM_BOT_TOKEN",
        "",
    ).strip()

    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not configured."
        )

    return token


def create_telegram_application() -> Application:
    """
    Create the Telegram application.

    The bot token is read from an environment variable.
    """

    token = get_bot_token()

    return (
        Application.builder()
        .token(token)
        .build()
    )
