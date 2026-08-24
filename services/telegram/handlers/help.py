from telegram import Update
from telegram.ext import ContextTypes


async def help_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    if update.message:
        await update.message.reply_text(
            "📚 راهنمای ربات\n\n"
            "📊 تحلیل هوشمند\n"
            "📡 سیگنال زنده\n"
            "🔎 اسکن بازار\n"
            "🧠 AI Coach\n"
            "📒 ژورنال معاملات\n"
            "⚙️ تنظیمات"
        )
