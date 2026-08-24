from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from ..state import update_menu, get_user_state
from ..scanner import scan_market, format_scan
from ..journal import format_journal, add_entry, JournalEntry
from ..coach import explain_report
from ..tracker import list_tracking, stop_tracking
from ..i18n import t
from analysis.full_engine import FullAnalysisEngine
from data.market_data import MarketDataEngine
from core.errors import ApplicationError


def main_menu_keyboard(language: str = "fa"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Smart Analysis" if language == "en" else "📊 تحلیل هوشمند", callback_data="analysis"), InlineKeyboardButton("📡 Live Signal" if language == "en" else "📡 سیگنال زنده", callback_data="signals")],
        [InlineKeyboardButton("🔎 Market Scanner" if language == "en" else "🔎 اسکن بازار", callback_data="scanner"), InlineKeyboardButton("🧠 AI Coach", callback_data="coach")],
        [InlineKeyboardButton("📒 Trading Journal" if language == "en" else "📒 ژورنال معاملات", callback_data="journal"), InlineKeyboardButton("⚙️ Settings" if language == "en" else "⚙️ تنظیمات", callback_data="settings")],
    ])


def submenu_keyboard(menu: str, language: str = "fa"):
    if menu == "analysis": buttons = [[InlineKeyboardButton(t(language, "quick"), callback_data="analysis_quick")], [InlineKeyboardButton(t(language, "full"), callback_data="analysis_full")]]
    elif menu == "signals": buttons = [[InlineKeyboardButton(t(language, "new_signal"), callback_data="signal_new")], [InlineKeyboardButton(t(language, "track"), callback_data="signal_track")]]
    elif menu == "settings": buttons = [[InlineKeyboardButton(t(language, "language"), callback_data="settings_language")], [InlineKeyboardButton(t(language, "analysis_mode"), callback_data="settings_analysis_mode")], [InlineKeyboardButton(t(language, "risk"), callback_data="settings_risk")], [InlineKeyboardButton(t(language, "market"), callback_data="settings_market")], [InlineKeyboardButton(t(language, "timeframe"), callback_data="settings_timeframe")], [InlineKeyboardButton(t(language, "notifications"), callback_data="settings_notifications")]]
    else: buttons = []
    buttons.append([InlineKeyboardButton(t(language, "back"), callback_data="home")])
    return InlineKeyboardMarkup(buttons)


def settings_keyboard(setting: str, language: str = "fa"):
    options = {
        "settings_language": [(t(language, "persian"), "language_fa"), (t(language, "english"), "language_en")],
        "settings_analysis_mode": [("Manual", "mode_manual"), ("Smart", "mode_smart"), ("Hybrid", "mode_hybrid")],
        "settings_risk": [("Low", "risk_low"), ("Medium", "risk_medium"), ("High", "risk_high")],
        "settings_market": [("EUR/USD", "market_EURUSD"), ("GBP/USD", "market_GBPUSD"), ("USD/JPY", "market_USDJPY"), ("XAU/USD", "market_XAUUSD")],
        "settings_timeframe": [("M5", "timeframe_M5"), ("M15", "timeframe_M15"), ("H1", "timeframe_H1"), ("H4", "timeframe_H4")],
        "settings_notifications": [("🔔 On" if language == "en" else "🔔 فعال", "notifications_on"), ("🔕 Off" if language == "en" else "🔕 خاموش", "notifications_off")],
    }
    buttons = [[InlineKeyboardButton(text, callback_data=data)] for text, data in options.get(setting, [])]
    buttons.append([InlineKeyboardButton(t(language, "settings_back"), callback_data="settings")])
    return InlineKeyboardMarkup(buttons)


def _apply_setting(state, data: str) -> str:
    if data == "language_fa": state.language = "fa"; return "زبان فارسی"
    if data == "language_en": state.language = "en"; return "English"
    if data.startswith("market_"): state.settings["market_symbol"] = data.removeprefix("market_"); return f"Market {state.settings['market_symbol']}"
    if data.startswith("timeframe_"): state.settings["timeframe"] = data.removeprefix("timeframe_"); return f"Timeframe {state.settings['timeframe']}"
    if data.startswith("mode_"): state.settings["analysis_mode"] = data.removeprefix("mode_"); return f"Analysis mode {state.settings['analysis_mode']}"
    if data.startswith("risk_"): state.settings["risk_level"] = data.removeprefix("risk_"); return f"Risk {state.settings['risk_level']}"
    if data == "notifications_on": state.settings["notifications_enabled"] = True; return "Notifications enabled"
    if data == "notifications_off": state.settings["notifications_enabled"] = False; return "Notifications disabled"
    return "Settings saved"


async def _run_signal_report(state):
    symbol = state.settings.get("market_symbol", "EURUSD"); timeframe = state.settings.get("timeframe", "M15")
    candles = await MarketDataEngine().get_candles_list(symbol, timeframe, 300)
    if not candles: raise RuntimeError("empty market data")
    return await __import__("asyncio").to_thread(FullAnalysisEngine().analyze, candles)


def _scanner_failure_text(language: str, error: Exception) -> str:
    if isinstance(error, ApplicationError) and error.details.get("required_environment"):
        required = ", ".join(error.details["required_environment"])
        if language == "en":
            return "❌ No market-data provider is configured on the server.\n\nAdd at least one real provider key to Railway environment variables:\n" + required
        return "❌ هیچ Provider داده بازار روی سرور فعال نیست.\n\nحداقل یکی از کلیدهای واقعی Provider را در Environment Variables ریل‌وی قرار بده:\n" + required
    return t(language, "scan_failed")


async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query: return
    await query.answer()
    data = query.data or "home"; user = update.effective_user; state = get_user_state(user.id) if user else None
    language = state.language if state else "fa"
    if user: update_menu(user.id, data)
    if data == "home": await query.edit_message_text(t(language, "home"), reply_markup=main_menu_keyboard(language)); return
    if data in ("analysis", "signals", "settings"):
        await query.edit_message_text(t(language, data), reply_markup=submenu_keyboard(data, language)); return
    if data == "scanner":
        if not state: return
        await query.edit_message_text("⏳ Scanning major markets..." if language == "en" else "⏳ در حال اسکن بازارهای اصلی...")
        try:
            timeframe = state.settings.get("timeframe", "M15"); results = await scan_market(timeframe=timeframe)
            await query.edit_message_text(format_scan(results, timeframe, language), parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(language, "retry"), callback_data="scanner")], [InlineKeyboardButton(t(language, "back"), callback_data="home")]]))
        except Exception as error:
            await query.edit_message_text(_scanner_failure_text(language, error), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(language, "retry"), callback_data="scanner")], [InlineKeyboardButton(t(language, "back"), callback_data="home")]]))
        return
    if data == "coach":
        if not state: return
        await query.edit_message_text("⏳ Building AI coach explanation..." if language == "en" else "⏳ در حال ساخت توضیح مربی...")
        try:
            report = await _run_signal_report(state); await query.edit_message_text(explain_report(report), parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(language, "retry"), callback_data="coach")], [InlineKeyboardButton(t(language, "back"), callback_data="home")]]))
        except Exception:
            await query.edit_message_text("❌ AI Coach could not obtain valid analysis." if language == "en" else "❌ مربی نتوانست تحلیل معتبر دریافت کند.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(language, "back"), callback_data="home")]]))
        return
    if data == "journal":
        if not user: return
        add_label = "➕ Add latest signal" if language == "en" else "➕ ثبت آخرین سیگنال معتبر"
        await query.edit_message_text(format_journal(user.id), parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(add_label, callback_data="journal_add")], [InlineKeyboardButton(t(language, "back"), callback_data="home")]])); return
    if data == "journal_add":
        if not user: return
        active = list_tracking(user.id)
        if not active:
            text = "ℹ️ No valid active signal is available to add to the journal." if language == "en" else "ℹ️ هیچ سیگنال معتبر و فعالی برای ثبت در ژورنال وجود ندارد."
        else:
            item = active[0]
            add_entry(user.id, JournalEntry(symbol=item.symbol, side=item.signal, entry=item.entry, stop_loss=item.stop_loss, take_profit=item.take_profit_1, notes="Added from active signal", status="OPEN"))
            text = "✅ Latest active signal added to the journal." if language == "en" else "✅ آخرین سیگنال معتبر در ژورنال ثبت شد."
        await query.edit_message_text(text + "\n\n" + format_journal(user.id), parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(language, "back"), callback_data="home")]])); return
    if data == "signal_track":
        if not user: return
        active = list_tracking(user.id)
        if not active:
            text = "📈 <b>Signal Tracking</b>\n\nNo active signal is being tracked." if language == "en" else "📈 <b>پیگیری سیگنال</b>\n\nسیگنال فعالی برای پیگیری ندارید."
            buttons = [[InlineKeyboardButton(t(language, "new_signal"), callback_data="signal_new")], [InlineKeyboardButton(t(language, "back"), callback_data="signals")]]
        else:
            lines = ["📈 <b>Tracked Signals</b>", ""]
            for item in active: lines.append(f"• {item.symbol}/{item.timeframe} → <b>{item.last_signal}</b> | {item.status} | {item.last_price or '—'}")
            text = "\n".join(lines); buttons = [[InlineKeyboardButton("⛔ Stop tracking" if language == "en" else "⛔ توقف پیگیری", callback_data="signal_untrack")], [InlineKeyboardButton("🔄 Refresh" if language == "en" else "🔄 بروزرسانی", callback_data="signal_track")], [InlineKeyboardButton(t(language, "back"), callback_data="signals")]]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons)); return
    if data == "signal_untrack":
        if user and state:
            removed = stop_tracking(user.id, state.settings.get("market_symbol", "EURUSD"), state.settings.get("timeframe", "M15"))
            text = ("⛔ Tracking stopped." if removed else "ℹ️ No active tracking found.") if language == "en" else ("⛔ پیگیری متوقف شد." if removed else "ℹ️ سیگنال فعالی پیدا نشد.")
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(language, "back"), callback_data="signals")]]))
        return
    if data.startswith("settings_"):
        await query.edit_message_text(t(language, "settings"), reply_markup=settings_keyboard(data, language)); return
    if data in {"analysis_quick", "analysis_full"}:
        if state: state.settings["analysis_mode"] = "smart" if data == "analysis_quick" else "full"
        await query.edit_message_text("📊 Analysis mode selected.\n\nUse New Signal to run live analysis." if language == "en" else "📊 حالت تحلیل انتخاب شد.\n\nبرای اجرای تحلیل زنده، روی سیگنال جدید بزنید.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(language, "new_signal"), callback_data="signal_new")], [InlineKeyboardButton(t(language, "back"), callback_data="analysis")]])); return
    if data == "signal_new":
        from .signal import signal_handler
        await signal_handler(update, context); return
    if state:
        message = _apply_setting(state, data)
        if data in {"language_fa", "language_en"}:
            language = state.language
            await query.edit_message_text(t(language, "home"), reply_markup=main_menu_keyboard(language)); return
    else: message = t(language, "saved")
    await query.edit_message_text(f"✅ {message}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(language, "settings_back"), callback_data="settings")]]))
