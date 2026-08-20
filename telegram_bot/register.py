from __future__ import annotations

from telegram.ext import Application, CommandHandler

from telegram_bot.handlers.start import start_handler


def register_handlers(
    app: Application,
) -> None:
    """
    Register all Telegram bot handlers.
    """

    handlers = [
        CommandHandler(
            "start",
            start_handler,
        ),
    ]

    for handler in handlers:
        app.add_handler(handler)
