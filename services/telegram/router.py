from telegram.ext import (
    Application,
    CommandHandler,
)

from services.telegram.handlers.start import (
    start_handler,
)


def register_routes(
    app: Application
) -> None:
    """
    Register telegram command routes.
    """

    app.add_handler(
        CommandHandler(
            "start",
            start_handler
        )
    )
