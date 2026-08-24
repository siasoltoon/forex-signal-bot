from telegram import Update
from telegram.ext import ContextTypes


async def signal_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    if update.message:
        await update.message.reply_text(
            "📡 بخش سیگنال\n\n"
            "موتور تصمیم‌گیری در حال اتصال است.\n"
            "در نسخه بعدی به Intelligence Pipeline متصل می‌شود."
        )
