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

    Core:
    - Trend
    - Market Structure
    - Score
    - Signal
    - Confidence

    Smart Money:
    - SMC Bias
    - Order Block
    - Liquidity
    - Fair Value Gap

    Confidence Layer:
    - Agreement
    - Votes
    - Warnings

    Explanation:
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
    # Confidence Layer
    # =========================


    agreement: float = 0.0


    bullish_votes: int = 0


    bearish_votes: int = 0


    warnings: list[str] = field(
        default_factory=list
    )



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
