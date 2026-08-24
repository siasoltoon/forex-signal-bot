from __future__ import annotations

from analysis.report import AnalysisReport


_SIGNAL_ACTIONS = {
    "STRONG_BUY": "خرید قوی فقط با رعایت حد ضرر و اندازه موقعیت مجاز است.",
    "BUY": "سناریوی خرید غالب است؛ ورود را با سطح ورود و حد ضرر گزارش تطبیق دهید.",
    "SELL": "سناریوی فروش غالب است؛ ورود را با سطح ورود و حد ضرر گزارش تطبیق دهید.",
    "STRONG_SELL": "فروش قوی است؛ همچنان مدیریت ریسک الزامی است.",
    "WAIT": "بهتر است تا افزایش هم‌جهتی تحلیل‌ها صبر کنید.",
    "NO_TRADE": "شرایط برای معامله مناسب نیست؛ فعلاً معامله نکنید.",
}


def explain_report(report: AnalysisReport) -> str:
    """Deterministic coaching based only on the production analysis report."""
    confidence = max(0.0, min(1.0, float(report.confidence))) * 100
    action = _SIGNAL_ACTIONS.get(str(report.signal).upper(), "فعلاً از ورود عجولانه خودداری کنید.")
    lines = [
        "🧠 <b>AI Coach — توضیح تصمیم</b>",
        "",
        f"بازار: <b>{report.symbol}</b>",
        f"تایم‌فریم: <b>{report.timeframe}</b>",
        f"تصمیم: <b>{str(report.signal).upper()}</b>",
        f"اطمینان: <b>{confidence:.1f}%</b>",
        f"کیفیت معامله: <b>{report.trade_grade}</b> ({report.trade_quality}/100)",
        "",
        f"💡 <b>اقدام پیشنهادی:</b> {action}",
    ]
    if report.reasons:
        lines.extend(["", "📌 <b>چرا؟</b>"])
        lines.extend(f"• {reason}" for reason in report.reasons[:6])
    if report.warnings:
        lines.extend(["", "⚠️ <b>چیزهایی که باید مراقبشان باشید:</b>"])
        lines.extend(f"• {warning}" for warning in report.warnings[:5])
    lines.extend([
        "",
        "🛡 این مربی سود قطعی وعده نمی‌دهد و در صورت نبود شرایط مناسب، گزینه عدم معامله را حفظ می‌کند.",
    ])
    return "\n".join(lines)


__all__ = ["explain_report"]
