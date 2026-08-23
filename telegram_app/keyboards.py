from __future__ import annotations

from .contracts import BotResponse


def main_menu(language: str = "fa") -> BotResponse:
    if language == "en":
        buttons = (("📊 Analysis", "analysis"), ("🔎 Scanner", "scanner"), ("⚙️ Settings", "settings"), ("📒 Journal", "journal"), ("📈 Portfolio", "portfolio"), ("ℹ️ Status", "status"))
        return BotResponse("Trading Intelligence Platform", buttons)
    buttons = (("📊 تحلیل", "analysis"), ("🔎 اسکنر", "scanner"), ("⚙️ تنظیمات", "settings"), ("📒 ژورنال", "journal"), ("📈 پرتفوی", "portfolio"), ("ℹ️ وضعیت", "status"))
    return BotResponse("پلتفرم هوشمندی بازار", buttons)


def analysis_menu(language: str = "fa") -> BotResponse:
    if language == "en":
        return BotResponse("Analysis setup", (("Market", "market"), ("Symbol", "symbol"), ("Timeframe", "timeframe"), ("Styles", "styles"), ("Presets", "presets"), ("Run analysis", "run_analysis")))
    return BotResponse("تنظیم تحلیل", (("بازار", "market"), ("نماد", "symbol"), ("تایم‌فریم", "timeframe"), ("سبک تحلیل", "styles"), ("پرسِت‌ها", "presets"), ("شروع تحلیل", "run_analysis")))
