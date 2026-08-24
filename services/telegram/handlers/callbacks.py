from telegram import Update
from telegram.ext import ContextTypes


MENU_RESPONSES = {
    "analysis": "📊 تحلیل هوشمند\n\nاین بخش به موتور تحلیل هوشمند متصل خواهد شد.",
    "signals": "📡 سیگنال زنده\n\nاین بخش به سیستم سیگنال متصل خواهد شد.",
    "scanner": "🔎 اسکن بازار\n\nاین بخش به Market Scanner متصل خواهد شد.",
    "coach": "🧠 AI Coach\n\nاین بخش برای مربی هوشمند معاملات آماده می‌شود.",
    "journal": "📒 ژورنال معاملات\n\nاین بخش به سیستم ثبت معاملات متصل خواهد شد.",
    "settings": "⚙️ تنظیمات\n\nتنظیمات ربات در این بخش قرار می‌گیرد.",
}


async def menu_callback_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if not query:
        return

    await query.answer()

    response = MENU_RESPONSES.get(
        query.data,
        "بخش موردنظر پیدا نشد."
    )

    await query.edit_message_text(response)
