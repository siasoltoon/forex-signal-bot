from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ..state import update_menu, get_user_state
from ..scanner import scan_market, format_scan
from ..journal import format_journal, add_entry, JournalEntry
from ..coach import explain_report
from ..tracker import list_tracking, stop_tracking
from analysis.full_engine import FullAnalysisEngine
from data.market_data import MarketDataEngine

MENU_RESPONSES = {"analysis": "📊 تحلیل هوشمند\n\nیک حالت تحلیل را انتخاب کنید.", "signals": "📡 سیگنال زنده\n\nیک گزینه را انتخاب کنید.", "scanner": "🔎 اسکن بازار", "coach": "🧠 AI Coach", "journal": "📒 ژورنال معاملات", "settings": "⚙️ تنظیمات\n\nیک گزینه تنظیمات را انتخاب کنید."}


def main_menu_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("📊 تحلیل هوشمند", callback_data="analysis"), InlineKeyboardButton("📡 سیگنال زنده", callback_data="signals")], [InlineKeyboardButton("🔎 اسکن بازار", callback_data="scanner"), InlineKeyboardButton("🧠 AI Coach", callback_data="coach")], [InlineKeyboardButton("📒 ژورنال معاملات", callback_data="journal"), InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings")]])


def submenu_keyboard(menu: str):
    if menu == "analysis": buttons = [[InlineKeyboardButton("⚡ تحلیل سریع", callback_data="analysis_quick")], [InlineKeyboardButton("📊 تحلیل کامل", callback_data="analysis_full")]]
    elif menu == "signals": buttons = [[InlineKeyboardButton("📡 سیگنال جدید", callback_data="signal_new")], [InlineKeyboardButton("📈 دنبال کردن سیگنال", callback_data="signal_track")]]
    elif menu == "settings": buttons = [[InlineKeyboardButton("🌐 زبان", callback_data="settings_language")], [InlineKeyboardButton("🧠 حالت تحلیل", callback_data="settings_analysis_mode")], [InlineKeyboardButton("⚖️ سطح ریسک", callback_data="settings_risk")], [InlineKeyboardButton("📊 بازار پیش‌فرض", callback_data="settings_market")], [InlineKeyboardButton("⏱ تایم‌فریم", callback_data="settings_timeframe")], [InlineKeyboardButton("🔔 اعلان‌ها", callback_data="settings_notifications")]]
    else: buttons = []
    buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="home")])
    return InlineKeyboardMarkup(buttons)


def settings_keyboard(setting: str):
    options = {"settings_language": [("🇮🇷 فارسی", "language_fa"), ("🇬🇧 English", "language_en")], "settings_analysis_mode": [("Manual", "mode_manual"), ("Smart", "mode_smart"), ("Hybrid", "mode_hybrid")], "settings_risk": [("Low", "risk_low"), ("Medium", "risk_medium"), ("High", "risk_high")], "settings_market": [("EUR/USD", "market_EURUSD"), ("GBP/USD", "market_GBPUSD"), ("USD/JPY", "market_USDJPY"), ("XAU/USD", "market_XAUUSD")], "settings_timeframe": [("M5", "timeframe_M5"), ("M15", "timeframe_M15"), ("H1", "timeframe_H1"), ("H4", "timeframe_H4")], "settings_notifications": [("🔔 فعال", "notifications_on"), ("🔕 خاموش", "notifications_off")]}
    buttons = [[InlineKeyboardButton(text, callback_data=data)] for text, data in options.get(setting, [])]
    buttons.append([InlineKeyboardButton("🔙 تنظیمات", callback_data="settings")])
    return InlineKeyboardMarkup(buttons)


def _apply_setting(state, data: str) -> str:
    if data == "language_fa": state.language = "fa"; return "زبان فارسی"
    if data == "language_en": state.language = "en"; return "English"
    if data.startswith("market_"): state.settings["market_symbol"] = data.removeprefix("market_"); return f"بازار {state.settings['market_symbol']}"
    if data.startswith("timeframe_"): state.settings["timeframe"] = data.removeprefix("timeframe_"); return f"تایم‌فریم {state.settings['timeframe']}"
    if data.startswith("mode_"): state.settings["analysis_mode"] = data.removeprefix("mode_"); return f"حالت تحلیل {state.settings['analysis_mode']}"
    if data.startswith("risk_"): state.settings["risk_level"] = data.removeprefix("risk_"); return f"ریسک {state.settings['risk_level']}"
    if data == "notifications_on": state.settings["notifications_enabled"] = True; return "اعلان‌ها فعال"
    if data == "notifications_off": state.settings["notifications_enabled"] = False; return "اعلان‌ها خاموش"
    state.settings[data] = True; return "تنظیمات ذخیره شد"


async def _run_signal_report(state):
    symbol = state.settings.get("market_symbol", "EURUSD"); timeframe = state.settings.get("timeframe", "M15")
    candles = await MarketDataEngine().get_candles_list(symbol, timeframe, 300)
    if not candles: raise RuntimeError("empty market data")
    return await __import__("asyncio").to_thread(FullAnalysisEngine().analyze, candles)


async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query: return
    await query.answer()
    data = query.data or "home"; user = update.effective_user; state = get_user_state(user.id) if user else None
    if user: update_menu(user.id, data)
    if data == "home": await query.edit_message_text("🤖 Forex AI Intelligence Platform\n\nیک بخش را انتخاب کنید:", reply_markup=main_menu_keyboard()); return
    if data in ("analysis", "signals", "settings"): await query.edit_message_text(MENU_RESPONSES[data], reply_markup=submenu_keyboard(data)); return
    if data == "scanner":
        if not state: return
        await query.edit_message_text("⏳ در حال اسکن بازارهای اصلی...")
        try:
            timeframe = state.settings.get("timeframe", "M15"); results = await scan_market(timeframe=timeframe)
            await query.edit_message_text(format_scan(results, timeframe), parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 اسکن دوباره", callback_data="scanner")], [InlineKeyboardButton("🔙 خانه", callback_data="home")]]))
        except Exception as exc: await query.edit_message_text(f"❌ اسکن انجام نشد: <code>{type(exc).__name__}</code>", parse_mode="HTML")
        return
    if data == "coach":
        if not state: return
        await query.edit_message_text("⏳ در حال ساخت توضیح مربی از آخرین تحلیل...")
        try:
            report = await _run_signal_report(state); await query.edit_message_text(explain_report(report), parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 تحلیل دوباره", callback_data="coach")], [InlineKeyboardButton("🔙 خانه", callback_data="home")]]))
        except Exception as exc: await query.edit_message_text(f"❌ مربی نتوانست تحلیل معتبر دریافت کند: <code>{type(exc).__name__}</code>", parse_mode="HTML")
        return
    if data == "journal":
        if not user: return
        await query.edit_message_text(format_journal(user.id), parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➕ ثبت نمونه معامله", callback_data="journal_add")], [InlineKeyboardButton("🔙 خانه", callback_data="home")]])); return
    if data == "journal_add":
        if user:
            symbol = state.settings.get("market_symbol", "EURUSD") if state else "EURUSD"; add_entry(user.id, JournalEntry(symbol=symbol, side="WATCH", entry=None, stop_loss=None, take_profit=None, notes="Created from Telegram"))
            await query.edit_message_text(format_journal(user.id), parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➕ ثبت دوباره", callback_data="journal_add")], [InlineKeyboardButton("🔙 خانه", callback_data="home")]]))
        return
    if data == "signal_track":
        if not user: return
        active = list_tracking(user.id)
        if not active:
            text = "📈 <b>پیگیری سیگنال</b>\n\nسیگنال فعالی برای پیگیری ندارید. ابتدا یک سیگنال BUY/SELL ایجاد کنید."
            buttons = [[InlineKeyboardButton("📡 سیگنال جدید", callback_data="signal_new")], [InlineKeyboardButton("🔙 بازگشت", callback_data="signals")]]
        else:
            lines = ["📈 <b>سیگنال‌های در حال پیگیری</b>", ""]
            for item in active: lines.append(f"• {item.symbol}/{item.timeframe} → <b>{item.last_signal}</b> | وضعیت: {item.status} | قیمت: {item.last_price or '—'}")
            text = "\n".join(lines); buttons = [[InlineKeyboardButton("⛔ توقف پیگیری", callback_data="signal_untrack")], [InlineKeyboardButton("🔄 بروزرسانی", callback_data="signal_track")], [InlineKeyboardButton("🔙 بازگشت", callback_data="signals")]]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons)); return
    if data == "signal_untrack":
        if user and state:
            symbol = state.settings.get("market_symbol", "EURUSD"); timeframe = state.settings.get("timeframe", "M15"); removed = stop_tracking(user.id, symbol, timeframe)
            await query.edit_message_text("⛔ پیگیری متوقف شد." if removed else "ℹ️ سیگنال فعالی برای این بازار/تایم‌فریم پیدا نشد.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 سیگنال‌ها", callback_data="signals")]]))
        return
    if data.startswith("settings_"): await query.edit_message_text("⚙️ یک گزینه را انتخاب کنید:", reply_markup=settings_keyboard(data)); return
    if data in {"analysis_quick", "analysis_full"}:
        if state: state.settings["analysis_mode"] = "smart" if data == "analysis_quick" else "full"
        await query.edit_message_text("📊 حالت تحلیل انتخاب شد.\n\nبرای اجرای تحلیل زنده، روی «سیگنال جدید» بزنید یا از /signal استفاده کنید.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📡 سیگنال جدید", callback_data="signal_new")], [InlineKeyboardButton("🔙 بازگشت", callback_data="analysis")]])); return
    if data == "signal_new":
        from .signal import signal_handler
        await signal_handler(update, context); return
    if state: message = _apply_setting(state, data)
    else: message = "تنظیمات ذخیره شد"
    await query.edit_message_text(f"✅ {message}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 تنظیمات", callback_data="settings")]]))
