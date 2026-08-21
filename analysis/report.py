from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any



# ==================================================
# Analysis Report
# ==================================================

@dataclass(
    frozen=True
)
class AnalysisReport:
    """
    Final user-facing analysis report.

    Contains:

    - Trend
    - Structure
    - Score
    - Signal
    - Confidence
    - Reasons
    - Indicators
    - Risk Plan
    """



    # =========================
    # Core Result
    # =========================

    trend: str

    structure: str

    score: float

    signal: str

    confidence: float



    # =========================
    # Explanation
    # =========================

    reasons: list[str] = field(
        default_factory=list
    )



    # =========================
    # Indicators
    # =========================

    indicators: dict[str, Any] = field(
        default_factory=dict
    )



    # =========================
    # Risk Management
    # =========================

    risk: Any = None
