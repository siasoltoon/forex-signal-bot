from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


MENU_RESPONSES = {
    "analysis": "📊 تحلیل هوشمند\n\nاین بخش به موتور تحلیل هوشمند متصل خواهد شد.",
    "signals": "📡 سیگنال زنده\n\nاین بخش به سیستم سیگنال متصل خواهد شد.",
    "scanner": "🔎 اسکن بازار\n\nاین بخش به Market Scanner متصل خواهد شد.",
    "coach": "🧠 AI Coach\n\nاین بخش برای مربی هوشمند معاملات آماده می‌شود.",
    "journal": "📒 ژورنال معاملات\n\nاین بخش به سیستم ثبت معاملات متصل خواهد شد.",
    "settings": "⚙️ تنظیمات\n\nتنظیمات ربات در این بخش قرار می‌گیرد.",
}


def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 تحلیل هوشمند", callback_data="analysis"),
         InlineKeyboardButton("📡 سیگنال زنده", callback_data="signals")],
        [InlineKeyboardButton("🔎 اسکن بازار", callback_data="scanner"),
         InlineKeyboardButton("🧠 AI Coach", callback_data="coach")],
        [InlineKeyboardButton("📒 ژورنال معاملات", callback_data="journal"),
         InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings")],
    ])


async def menu_callback_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if not query:
        return

    await query.answer()

    if query.data == "settings":
        await query.edit_message_text(
            "⚙️ تنظیمات\n\nتنظیمات ربات در این بخش قرار می‌گیرد."
        )
        return

    response = MENU_RESPONSES.get(
        query.data,
        "بخش موردنظر پیدا نشد."
    )

    await query.edit_message_text(
        response,
        reply_markup=main_menu_keyboard(),
    )
