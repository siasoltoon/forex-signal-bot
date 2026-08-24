from telegram import Update
from telegram.ext import ContextTypes


async def status_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    if update.message:
        await update.message.reply_text(
            "🟢 وضعیت سیستم\n\n"
            "Telegram: Online\n"
            "Application: Running"
        )
