from __future__ import annotations

from typing import Any, Mapping


def render_analysis_report(report: Mapping[str, Any], language: str = "fa") -> str:
    labels_fa = {
        "market": "بازار", "symbol": "نماد", "timeframe": "تایم‌فریم",
        "regime": "رژیم بازار", "decision": "تصمیم", "confidence": "میزان اطمینان",
        "risk": "ریسک", "data_quality": "کیفیت داده",
    }
    labels = labels_fa if language == "fa" else {key: key.replace("_", " ").title() for key in report}
    lines = [f"{labels.get(key, key)}: {value}" for key, value in report.items()]
    return "📊 گزارش تحلیل\n\n" + "\n".join(lines) if language == "fa" else "📊 Analysis Report\n\n" + "\n".join(lines)
