from telegram import Update
from telegram.ext import ContextTypes


async def start_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handle /start command.
    """

    if update.message:

        await update.message.reply_text(
            "🤖 سلام!\n\n"
            "به ربات تحلیل هوشمند فارکس خوش آمدید.\n"
            "سیستم در حال آماده‌سازی است."
        )
