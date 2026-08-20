import os

from telegram.ext import Application

from telegram_bot.register import register_handlers


def get_bot_token():
    return os.getenv("TELEGRAM_BOT_TOKEN")


def create_bot():
    token = get_bot_token()

    if not token:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN is not set"
        )

    app = Application.builder().token(token).build()

    register_handlers(app)

    return app
