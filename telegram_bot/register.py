from telegram.ext import Application, CommandHandler

from telegram_bot.handlers.start import start_handler


def register_handlers(app: Application):
    app.add_handler(
        CommandHandler(
            "start",
            start_handler
        )
    )
