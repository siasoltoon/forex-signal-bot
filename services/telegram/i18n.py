from __future__ import annotations

TRANSLATIONS = {
    "fa": {
        "home": "🤖 پلتفرم هوش فارکس\n\nیک بخش را انتخاب کنید:",
        "analysis": "📊 تحلیل هوشمند\n\nیک حالت تحلیل را انتخاب کنید.",
        "signals": "📡 سیگنال زنده\n\nیک گزینه را انتخاب کنید.",
        "scanner": "🔎 اسکن بازار",
        "coach": "🧠 مربی هوش مصنوعی",
        "journal": "📒 ژورنال معاملات",
        "settings": "⚙️ تنظیمات\n\nیک گزینه تنظیمات را انتخاب کنید.",
        "language": "🌐 زبان", "analysis_mode": "🧠 حالت تحلیل", "risk": "⚖️ سطح ریسک",
        "market": "📊 بازار پیش‌فرض", "timeframe": "⏱ تایم‌فریم", "notifications": "🔔 اعلان‌ها",
        "back": "🔙 بازگشت", "settings_back": "🔙 تنظیمات", "english": "🇬🇧 English", "persian": "🇮🇷 فارسی",
        "scan_unavailable": "داده یا تحلیل معتبر برای این نماد در دسترس نیست.",
        "scan_note": "ℹ️ فقط خروجی حاصل از داده معتبر و موتور تحلیل واقعی نمایش داده می‌شود.",
        "scan_failed": "❌ اسکن بازار در حال حاضر قابل انجام نیست. لطفاً کمی بعد دوباره تلاش کنید.",
        "saved": "تنظیمات ذخیره شد.", "quick": "⚡ تحلیل سریع", "full": "📊 تحلیل کامل",
        "new_signal": "📡 سیگنال جدید", "track": "📈 دنبال کردن سیگنال", "retry": "🔄 دوباره تلاش کنید",
    },
    "en": {
        "home": "🤖 Forex AI Intelligence Platform\n\nChoose a section:",
        "analysis": "📊 Smart Analysis\n\nChoose an analysis mode.",
        "signals": "📡 Live Signal\n\nChoose an option.",
        "scanner": "🔎 Market Scanner", "coach": "🧠 AI Coach", "journal": "📒 Trading Journal",
        "settings": "⚙️ Settings\n\nChoose a setting.",
        "language": "🌐 Language", "analysis_mode": "🧠 Analysis Mode", "risk": "⚖️ Risk Level",
        "market": "📊 Default Market", "timeframe": "⏱ Timeframe", "notifications": "🔔 Notifications",
        "back": "🔙 Back", "settings_back": "🔙 Settings", "english": "🇬🇧 English", "persian": "🇮🇷 Persian",
        "scan_unavailable": "Valid data or analysis is unavailable for this symbol.",
        "scan_note": "ℹ️ Only results from valid data and the real analysis engine are shown.",
        "scan_failed": "❌ Market scanning is currently unavailable. Please try again later.",
        "saved": "Settings saved.", "quick": "⚡ Quick Analysis", "full": "📊 Full Analysis",
        "new_signal": "📡 New Signal", "track": "📈 Track Signal", "retry": "🔄 Retry",
    },
}


def t(language: str, key: str, **kwargs) -> str:
    table = TRANSLATIONS.get(language, TRANSLATIONS["fa"])
    text = table.get(key, TRANSLATIONS["fa"].get(key, key))
    return text.format(**kwargs)


__all__ = ["t", "TRANSLATIONS"]
