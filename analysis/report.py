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
    - Market structure
    - Final score
    - Signal
    - Confidence
    - Smart Money Concepts
    - Reasons
    - Indicators
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
    # Smart Money Concepts
    # =========================

    smc_bias: str = "neutral"


    smc_structure: str = "none"


    order_block: str = "none"


    liquidity: str = "none"


    fair_value_gap: bool = False


    premium_discount: str = "none"



    # =========================
    # Explanation Layer
    # =========================

    reasons: list[str] = field(
        default_factory=list
    )



    # =========================
    # Indicator Snapshot
    # =========================

    indicators: dict[str, Any] = field(
        default_factory=dict
    )
