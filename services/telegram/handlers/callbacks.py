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
            [InlineKeyboardButton("⏱ تایم‌فریم", callback_data="settings_timeframe")],
            [InlineKeyboardButton("🔔 اعلان‌ها", callback_data="settings_notifications")],
        ]
    else:
        buttons = []

    buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="home")])
    return InlineKeyboardMarkup(buttons)


def settings_keyboard(setting: str):
    options = {
        "settings_language": [("🇮🇷 فارسی", "language_fa"), ("🇬🇧 English", "language_en")],
        "settings_analysis_mode": [("Manual", "mode_manual"), ("Smart", "mode_smart"), ("Hybrid", "mode_hybrid")],
        "settings_risk": [("Low", "risk_low"), ("Medium", "risk_medium"), ("High", "risk_high")],
        "settings_market": [("EUR/USD", "market_EURUSD"), ("GBP/USD", "market_GBPUSD"), ("USD/JPY", "market_USDJPY"), ("XAU/USD", "market_XAUUSD")],
        "settings_timeframe": [("M5", "timeframe_M5"), ("M15", "timeframe_M15"), ("H1", "timeframe_H1"), ("H4", "timeframe_H4")],
        "settings_notifications": [("🔔 فعال", "notifications_on"), ("🔕 خاموش", "notifications_off")],
    }
    buttons = [[InlineKeyboardButton(text, callback_data=data)] for text, data in options.get(setting, [])]
    buttons.append([InlineKeyboardButton("🔙 تنظیمات", callback_data="settings")])
    return InlineKeyboardMarkup(buttons)


def _apply_setting(state, data: str) -> str:
    if data == "language_fa":
        state.language = "fa"
        return "زبان فارسی"
    if data == "language_en":
        state.language = "en"
        return "English"
    if data.startswith("market_"):
        state.settings["market_symbol"] = data.removeprefix("market_")
        return f"بازار {state.settings['market_symbol']}"
    if data.startswith("timeframe_"):
        state.settings["timeframe"] = data.removeprefix("timeframe_")
        return f"تایم‌فریم {state.settings['timeframe']}"
    if data.startswith("mode_"):
        state.settings["analysis_mode"] = data.removeprefix("mode_")
        return f"حالت تحلیل {state.settings['analysis_mode']}"
    if data.startswith("risk_"):
        state.settings["risk_level"] = data.removeprefix("risk_")
        return f"ریسک {state.settings['risk_level']}"
    if data == "notifications_on":
        state.settings["notifications_enabled"] = True
        return "اعلان‌ها فعال"
    if data == "notifications_off":
        state.settings["notifications_enabled"] = False
        return "اعلان‌ها خاموش"
    state.settings[data] = True
    return "تنظیمات ذخیره شد"


async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return

    await query.answer()
    data = query.data or "home"
    user = update.effective_user
    state = get_user_state(user.id) if user else None

    if user:
        update_menu(user.id, data)

    if data == "home":
        await query.edit_message_text(
            "🤖 Forex AI Intelligence Platform\n\nیک بخش را انتخاب کنید:",
            reply_markup=main_menu_keyboard(),
        )
        return

    if data in ("analysis", "signals", "settings"):
        await query.edit_message_text(MENU_RESPONSES[data], reply_markup=submenu_keyboard(data))
        return

    if data.startswith("settings_"):
        await query.edit_message_text("⚙️ یک گزینه را انتخاب کنید:", reply_markup=settings_keyboard(data))
        return

    if data in {"analysis_quick", "analysis_full"}:
        if state:
            state.settings["analysis_mode"] = "smart" if data == "analysis_quick" else "full"
        await query.edit_message_text(
            "📊 حالت تحلیل انتخاب شد.\n\nبرای اجرای تحلیل زنده، روی «سیگنال جدید» بزنید یا از /signal استفاده کنید.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📡 سیگنال جدید", callback_data="signal_new")], [InlineKeyboardButton("🔙 بازگشت", callback_data="analysis")]]),
        )
        return

    if data == "signal_new":
        from .signal import signal_handler
        await signal_handler(update, context)
        return

    if data == "signal_track":
        await query.edit_message_text(
            "📈 دنبال‌کردن سیگنال در نسخه فعلی فقط پس از تولید سیگنال فعال می‌شود.\n\nابتدا «سیگنال جدید» را اجرا کنید.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📡 سیگنال جدید", callback_data="signal_new")], [InlineKeyboardButton("🔙 بازگشت", callback_data="signals")]]),
        )
        return

    if data in {"scanner", "coach", "journal"}:
        await query.edit_message_text(
            f"{MENU_RESPONSES[data]}\n\nاین بخش هنوز به سرویس اجرایی مربوطه متصل نشده و سیگنال/اطلاعات ساختگی نمایش داده نمی‌شود.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="home")]]),
        )
        return

    if state:
        message = _apply_setting(state, data)
    else:
        message = "تنظیمات ذخیره شد"

    await query.edit_message_text(
        f"✅ {message}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 تنظیمات", callback_data="settings")]]),
    )
