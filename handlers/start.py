from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes


async def start_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handles the /start command.
    """

    if update.message is None:
        return

    await update.message.reply_text(
        "🤖 Forex Signal Bot\n\n"
        "ربات با موفقیت فعال است.\n\n"
        "در نسخه‌های بعدی امکانات تحلیل بازار "
        "و مدیریت سیگنال به آن اضافه می‌شود."
    )
