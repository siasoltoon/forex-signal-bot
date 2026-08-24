from telegram import Update
from telegram.ext import ContextTypes


async def settings_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle settings menu."""

    if update.message:
        await update.message.reply_text(
            "⚙️ تنظیمات\n\n"
            "تنظیمات کاربر در نسخه بعدی تکمیل می‌شود."
        )
