from __future__ import annotations

import os

from telegram.ext import Application

from handlers.register import register_handlers


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
    Create and configure the Telegram application.
    """

    token = get_bot_token()

    application = (
        Application.builder()
        .token(token)
        .build()
    )

    register_handlers(
        application
    )

    return application
