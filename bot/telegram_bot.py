import logging

from telegram.ext import Application

from bot.handlers import register_handlers
from config.settings import settings


logger = logging.getLogger(__name__)


def create_application() -> Application:
    """
    Create and configure the Telegram application.
    """

    application = (
        Application.builder()
        .token(settings.BOT_TOKEN)
        .build()
    )

    register_handlers(application)

    logger.info("Telegram application configured.")

    return application
