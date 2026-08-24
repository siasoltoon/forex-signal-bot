from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
)

from services.telegram.handlers.start import start_handler
from services.telegram.handlers.help import help_handler
from services.telegram.handlers.status import status_handler
from services.telegram.handlers.signal import signal_handler
from services.telegram.handlers.callbacks import menu_callback_handler


def register_routes(
    app: Application
) -> None:
    """Register telegram command and callback routes."""

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("status", status_handler))
    app.add_handler(CommandHandler("signal", signal_handler))

    app.add_handler(
        CallbackQueryHandler(menu_callback_handler)
    )
