from __future__ import annotations

import os

from telegram.ext import Application

from telegram_bot.register import register_handlers


def get_bot_token() -> str | None:
    """
    Get Telegram bot token from environment variables.
    """

    return os.getenv("TELEGRAM_BOT_TOKEN")


def create_bot() -> Application:
    """
    Create and configure Telegram bot application.
    """

    token = get_bot_token()

    if not token:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN is not set"
        )

    bot_app = (
        Application
        .builder()
        .token(token)
        .build()
    )

    register_handlers(bot_app)

    return bot_app


def run_bot() -> None:
    """
    Start Telegram bot using polling.
    """

    bot_app = create_bot()

    bot_app.run_polling()
