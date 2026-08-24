from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ..state import update_menu


MENU_RESPONSES = {
    "analysis": "📊 تحلیل هوشمند\n\nیک حالت تحلیل را انتخاب کنید.",
    "signals": "📡 سیگنال زنده\n\nیک گزینه را انتخاب کنید.",
    "scanner": "🔎 اسکن بازار\n\nبازار موردنظر را انتخاب کنید.",
    "coach": "🧠 AI Coach\n\nبخش مربی هوشمند آماده اتصال است.",
    "journal": "📒 ژورنال معاملات\n\nسوابق معاملات شما اینجا نمایش داده می‌شود.",
    "settings": "⚙️ تنظیمات\n\nتنظیمات ربات را مدیریت کنید.",
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


def submenu_keyboard(menu: str):
    if menu == "analysis":
        buttons = [
            [InlineKeyboardButton("⚡ تحلیل سریع", callback_data="analysis_quick")],
            [InlineKeyboardButton("📊 تحلیل کامل", callback_data="analysis_full")],
        ]
    elif menu == "signals":
        buttons = [
            [InlineKeyboardButton("📡 سیگنال جدید", callback_data="signal_new")],
            [InlineKeyboardButton("📈 دنبال کردن سیگنال", callback_data="signal_track")],
        ]
    else:
        buttons = []

    buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="home")])
    return InlineKeyboardMarkup(buttons)


async def menu_callback_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if not query:
        return

    await query.answer()

    user = update.effective_user
    if user:
        update_menu(user.id, query.data or "home")

    if query.data == "home":
        await query.edit_message_text(
            "🤖 Forex AI Intelligence Platform\n\nیک بخش را انتخاب کنید:",
            reply_markup=main_menu_keyboard(),
        )
        return

    if query.data in ("analysis", "signals"):
        await query.edit_message_text(
            MENU_RESPONSES[query.data],
            reply_markup=submenu_keyboard(query.data),
        )
        return

    response = MENU_RESPONSES.get(query.data, "❌ بخش موردنظر پیدا نشد.")

    await query.edit_message_text(
        response,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت", callback_data="home")]
        ]),
    )
