from __future__ import annotations
import logging

from telegram import Update
from telegram.ext import ContextTypes

from analysis.contracts import AnalysisContext
from services.telegram.state import get_user_state
from services.telegram.tracker import track_report
from services.analysis.signal_adapter import adapt_analysis_run

logger = logging.getLogger(__name__)

DEFAULT_SYMBOL = "EURUSD"
DEFAULT_TIMEFRAME = "M15"
_SIGNAL_LABELS = {"STRONG_BUY":"🟢 خرید قوی","BUY":"🟢 خرید","WAIT":"🟡 انتظار","NO_TRADE":"⛔ عدم معامله","SELL":"🔴 فروش","STRONG_SELL":"🔴 فروش قوی"}


def _setting_value(state, key: str, default: str) -> str:
    value = state.settings.get(key, default)
    return value if isinstance(value, str) and value.strip() else default


def _format_price(value: float | None) -> str:
    return "—" if value is None else f"{value:.5f}"


def _format_number(value: float | None) -> str:
    return "—" if value is None else f"{value:.2f}"


def _format_signal(report, symbol: str, timeframe: str) -> str:
    signal = str(report.signal).upper()
    confidence = max(0.0, min(1.0, float(report.confidence))) * 100.0
    lines = ["📡 <b>سیگنال جدید</b>", "", f"💱 بازار: <b>{symbol}</b>", f"⏱ تایم‌فریم: <b>{timeframe}</b>", f"📌 تصمیم: <b>{_SIGNAL_LABELS.get(signal, signal)}</b>", f"📊 امتیاز: <b>{_format_number(report.score)}</b>", f"🎯 اطمینان: <b>{confidence:.1f}%</b>", f"🏆 کیفیت معامله: <b>{report.trade_grade}</b> ({report.trade_quality}/100)", f"📈 روند: <b>{report.trend}</b>", f"🧭 ساختار: <b>{report.structure}</b>", "", "💰 <b>سطوح مدیریت معامله</b>", f"ورود: <b>{_format_price(report.entry_price)}</b>", f"حد ضرر: <b>{_format_price(report.stop_loss)}</b>", f"هدف ۱: <b>{_format_price(report.take_profit_1)}</b>", f"هدف ۲: <b>{_format_price(report.take_profit_2)}</b>", f"هدف ۳: <b>{_format_price(report.take_profit_3)}</b>", f"⚖️ نسبت ریسک/بازده: <b>{_format_number(report.risk_reward)}</b>"]
    if report.warnings:
        lines.extend(["", "⚠️ <b>هشدارها</b>"])
        lines.extend(f"• {warning}" for warning in report.warnings[:5])
    if report.reasons:
        lines.extend(["", "🧠 <b>دلایل اصلی</b>"])
        lines.extend(f"• {reason}" for reason in report.reasons[:6])
    return "\n".join(lines)


async def signal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Run signal generation through AnalysisService and Live Signal Engine."""
    source_message = update.message or (update.callback_query.message if update.callback_query else None)
    if source_message is None:
        return

    if update.callback_query:
        await update.callback_query.answer()

    user_id = update.effective_user.id if update.effective_user else None
    state = get_user_state(user_id) if user_id is not None else None
    symbol = _setting_value(state, "market_symbol", DEFAULT_SYMBOL) if state else DEFAULT_SYMBOL
    timeframe = _setting_value(state, "timeframe", DEFAULT_TIMEFRAME) if state else DEFAULT_TIMEFRAME

    status_message = await source_message.reply_text(f"⏳ در حال اجرای تحلیل {symbol}/{timeframe}...")

    try:
        analysis_service = context.bot_data.get("analysis_service")
        if analysis_service is None:
            raise RuntimeError("analysis service unavailable")

        market_data = context.bot_data.get("market_data_provider")
        if market_data is None:
            raise RuntimeError("market data provider unavailable")

        candles = await market_data.get_candles_list(symbol=symbol, timeframe=timeframe, limit=300)
        if not candles:
            raise RuntimeError("empty market data")

        run = analysis_service.analyze(
            AnalysisContext(
                symbol=symbol,
                timeframe=timeframe,
                data=candles,
                metadata={"source": "telegram"},
            )
        )

        report = adapt_analysis_run(run, symbol=symbol, timeframe=timeframe)

        signal_engine = context.bot_data.get("signal_engine")
        if signal_engine and str(report.signal).upper() not in {"WAIT", "NO_TRADE"}:
            signal_engine.create_signal(
                report,
                symbol=symbol,
                timeframe=timeframe,
            )

        if user_id is not None and str(report.signal).upper() not in {"WAIT", "NO_TRADE"}:
            track_report(user_id, symbol, timeframe, report)

        await status_message.edit_text(_format_signal(report, symbol, timeframe), parse_mode="HTML")

    except Exception as exc:
        logger.exception("Signal generation failed for %s/%s", symbol, timeframe, exc_info=exc)
        await status_message.edit_text("❌ <b>سیگنال قابل تولید نیست.</b>\n\nموتور تحلیل نتیجه معتبر ارائه نکرد.", parse_mode="HTML")
