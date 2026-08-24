from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


MENU_RESPONSES = {
    "analysis": "📊 تحلیل هوشمند\n\nاین بخش آماده اتصال به موتور تحلیل هوشمند است.",
    "signals": "📡 سیگنال زنده\n\nاین بخش آماده اتصال به Decision Engine است.",
    "scanner": "🔎 اسکن بازار\n\nاین بخش آماده اتصال به Market Scanner است.",
    "coach": "🧠 AI Coach\n\nاین بخش آماده اتصال به مربی هوشمند معاملات است.",
    "journal": "📒 ژورنال معاملات\n\nاین بخش آماده اتصال به Persistence Layer است.",
    "settings": "⚙️ تنظیمات\n\nتنظیمات ربات از این بخش مدیریت می‌شود.",
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


def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="home")]
    ])


async def menu_callback_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if not query:
        return

    await query.answer()

    if query.data == "home":
        await query.edit_message_text(
            "🤖 Forex AI Intelligence Platform\n\nیک بخش را انتخاب کنید:",
            reply_markup=main_menu_keyboard(),
        )
        return

    response = MENU_RESPONSES.get(
        query.data,
        "❌ بخش موردنظر پیدا نشد."
    )

    await query.edit_message_text(
        response,
        reply_markup=back_keyboard(),
    )
