from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ReportPreferences:
    language: str = "fa"
    detail_level: str = "advanced"
    show_reasons: bool = True
    show_scenarios: bool = True
    show_risk: bool = True


class TelegramReportBuilder:
    """Presentation-only layer; it never creates trading facts."""
    def build(self, result: object, preferences: ReportPreferences | None = None) -> str:
        p = preferences or ReportPreferences()
        decision = getattr(getattr(result, "decision", None), "decision", "NO TRADE")
        confidence = getattr(getattr(result, "decision", None), "confidence", 0.0)
        if p.language.lower().startswith("en"):
            return f"Decision: {decision}\nConfidence: {confidence:.1f}/100"
        return f"تصمیم: {decision}\nمیزان اطمینان: {confidence:.1f}/100"
