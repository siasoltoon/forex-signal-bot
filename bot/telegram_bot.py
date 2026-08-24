import logging

from telegram.ext import Application

from bot.handlers import register_handlers
from config.settings import settings
from services.telegram.tracker_job import refresh_all_tracked_signals


logger = logging.getLogger(__name__)


def create_application() -> Application:
    """Create and configure the Telegram application and lifecycle monitor."""
    application = Application.builder().token(settings.BOT_TOKEN).build()
    register_handlers(application)

    if application.job_queue is not None:
        application.job_queue.run_repeating(refresh_all_tracked_signals, interval=300, first=30, name="signal-lifecycle-monitor")
    else:
        logger.warning("Telegram JobQueue unavailable; signal lifecycle monitor is disabled.")

    logger.info("Telegram application configured.")
    return application
