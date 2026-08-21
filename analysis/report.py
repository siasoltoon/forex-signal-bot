from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any



@dataclass(
    frozen=True
)
class AnalysisReport:
    """
    Final user-facing analysis report.

    Contains:
    - Trend
    - Market structure
    - Score
    - Signal
    - Confidence
    - Reasons
    - Indicators
    - Smart Money Concepts data
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


    smc_structure: str = "unknown"


    order_block: dict[str, Any] | None = None


    liquidity: dict[str, Any] | None = None


    fair_value_gap: dict[str, Any] | None = None


    premium_discount: str = "unknown"



    # =========================
    # Explanation Layer
    # =========================

    reasons: list[str] = field(
        default_factory=list
    )



    # =========================
    # Indicators Snapshot
    # =========================

    indicators: dict[str, Any] = field(
        default_factory=dict
    )
