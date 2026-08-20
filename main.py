import logging

from bot.telegram_bot import create_application
from config.settings import settings
from utils.logger import setup_logger


def main() -> None:
    """
    Application entry point.
    """

    setup_logger(settings.LOG_LEVEL)

    logger = logging.getLogger(__name__)

    logger.info(
        "Starting Forex Signal Bot..."
    )

    logger.info(
        "Environment: %s",
        settings.ENVIRONMENT,
    )

    application = create_application()

    logger.info(
        "Telegram bot is starting..."
    )

    application.run_polling(
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
