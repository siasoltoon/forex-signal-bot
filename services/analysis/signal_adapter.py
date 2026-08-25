from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from analysis.contracts import AnalysisRun


@dataclass(frozen=True)
class SignalAnalysisResult:
    """Compatibility envelope between AnalysisService and Telegram signals."""

    signal: str = "NO_TRADE"
    confidence: float = 0.0
    score: float = 0.0
    trade_grade: str = "N/A"
    trade_quality: float = 0.0
    trend: str = "UNKNOWN"
    structure: str = "UNKNOWN"
    entry_price: float | None = None
    stop_loss: float | None = None
    take_profit_1: float | None = None
    take_profit_2: float | None = None
    take_profit_3: float | None = None
    risk_reward: float | None = None
    warnings: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()


def adapt_analysis_run(run: AnalysisRun) -> SignalAnalysisResult:
    """Convert the generic analysis pipeline output to signal UI format.

    Keeps Telegram compatibility while the analysis architecture evolves.
    """
    values: dict[str, Any] = {}

    for result in run.successful:
        values.update(result.values)

    return SignalAnalysisResult(
        signal=str(values.get("signal", "NO_TRADE")),
        confidence=float(values.get("confidence", 0.0) or 0.0),
        score=float(values.get("score", 0.0) or 0.0),
        trade_grade=str(values.get("trade_grade", "N/A")),
        trade_quality=float(values.get("trade_quality", 0.0) or 0.0),
        trend=str(values.get("trend", "UNKNOWN")),
        structure=str(values.get("structure", "UNKNOWN")),
        entry_price=values.get("entry_price"),
        stop_loss=values.get("stop_loss"),
        take_profit_1=values.get("take_profit_1"),
        take_profit_2=values.get("take_profit_2"),
        take_profit_3=values.get("take_profit_3"),
        risk_reward=values.get("risk_reward"),
        warnings=tuple(values.get("warnings", ()) or ()),
        reasons=tuple(values.get("reasons", ()) or ()),
    )
