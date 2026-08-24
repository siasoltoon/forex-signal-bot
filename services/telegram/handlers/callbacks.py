from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ..state import update_menu, get_user_state


MENU_RESPONSES = {
    "analysis": "📊 تحلیل هوشمند\n\nیک حالت تحلیل را انتخاب کنید.",
    "signals": "📡 سیگنال زنده\n\nیک گزینه را انتخاب کنید.",
    "scanner": "🔎 اسکن بازار\n\nبازار موردنظر را انتخاب کنید.",
    "coach": "🧠 AI Coach\n\nبخش مربی هوشمند آماده اتصال است.",
    "journal": "📒 ژورنال معاملات\n\nسوابق معاملات شما اینجا نمایش داده می‌شود.",
    "settings": "⚙️ تنظیمات\n\nیک گزینه تنظیمات را انتخاب کنید.",
}


def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 تحلیل هوشمند", callback_data="analysis"), InlineKeyboardButton("📡 سیگنال زنده", callback_data="signals")],
        [InlineKeyboardButton("🔎 اسکن بازار", callback_data="scanner"), InlineKeyboardButton("🧠 AI Coach", callback_data="coach")],
        [InlineKeyboardButton("📒 ژورنال معاملات", callback_data="journal"), InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings")],
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
    elif menu == "settings":
        buttons = [
            [InlineKeyboardButton("🌐 زبان", callback_data="settings_language")],
            [InlineKeyboardButton("🧠 حالت تحلیل", callback_data="settings_analysis_mode")],
            [InlineKeyboardButton("⚖️ سطح ریسک", callback_data="settings_risk")],
            [InlineKeyboardButton("📊 بازار پیش‌فرض", callback_data="settings_market")],
            [InlineKeyboardButton("🔔 اعلان‌ها", callback_data="settings_notifications")],
        ]
    else:
        buttons = []

    buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="home")])
    return InlineKeyboardMarkup(buttons)


def settings_keyboard(setting: str):
    options = {
        "settings_language": [
            ("🇮🇷 فارسی", "language_fa"),
            ("🇬🇧 English", "language_en"),
        ],
        "settings_analysis_mode": [
            ("Manual", "mode_manual"),
            ("Smart", "mode_smart"),
            ("Hybrid", "mode_hybrid"),
        ],
        "settings_risk": [
            ("Low", "risk_low"),
            ("Medium", "risk_medium"),
            ("High", "risk_high"),
        ],
        "settings_market": [
            ("Forex", "market_forex"),
            ("Crypto", "market_crypto"),
            ("Gold", "market_gold"),
            ("Stocks", "market_stocks"),
        ],
        "settings_notifications": [
            ("🔔 فعال", "notifications_on"),
            ("🔕 خاموش", "notifications_off"),
        ],
    }

    buttons = [[InlineKeyboardButton(text, callback_data=data)] for text, data in options.get(setting, [])]
    buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="settings")])
    return InlineKeyboardMarkup(buttons)


async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

    if query.data in ("analysis", "signals", "settings"):
        await query.edit_message_text(
            MENU_RESPONSES[query.data],
            reply_markup=submenu_keyboard(query.data),
        )
        return

    if query.data.startswith("settings_"):
        await query.edit_message_text(
            "⚙️ یک گزینه را انتخاب کنید:",
            reply_markup=settings_keyboard(query.data),
        )
        return

    if user:
        state = get_user_state(user.id)
        state.settings[query.data] = True

    await query.edit_message_text(
        "✅ تنظیمات ذخیره شد.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 تنظیمات", callback_data="settings")]]),
    )
