from __future__ import annotations

from telegram.ext import Application, CommandHandler

from handlers.start import start_handler


def register_handlers(
    application: Application,
) -> None:
    """
    Register all Telegram bot handlers.
    """

    application.add_handler(
        CommandHandler(
            "start",
            start_handler,
        )
    )
