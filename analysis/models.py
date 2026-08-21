from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from analysis.candle import Candle



# ==================================================
# Signal Component
# ==================================================

@dataclass(
    frozen=True
)
class SignalComponent:
    """
    Single scoring component.
    """

    name: str

    score: float

    reason: str



# ==================================================
# Analysis Score
# ==================================================

@dataclass(
    frozen=True
)
class AnalysisScore:
    """
    Final scoring result.
    """

    score: float

    direction: str

    confidence: float

    components: list[SignalComponent] = field(
        default_factory=list
    )



# ==================================================
# Complete Analysis Result
# ==================================================

@dataclass(
    frozen=True
)
class AnalysisResult:
    """
    Complete technical analysis state.
    """


    # =========================
    # Core Analysis
    # =========================

    trend: str

    momentum: str

    indicators: dict[str, Any]


    candles: list[Candle] = field(
        default_factory=list
    )



    # =========================
    # Supply Demand
    # =========================

    supply_demand: Any = None



    # =========================
    # Core Scores
    # =========================

    trend_score: float = 0.0

    momentum_score: float = 0.0

    structure_score: float = 0.0

    volatility_score: float = 0.0

    price_action_score: float = 0.0



    # =========================
    # Pattern Scores
    # =========================

    candlestick_score: float = 0.0

    elliott_score: float = 0.0

    harmonic_score: float = 0.0

    brooks_score: float = 0.0

    wyckoff_score: float = 0.0


    
    # =========================
    # Smart Money Concepts
    # =========================

    smart_money_score: float = 0.0


    smc_bias: str = "neutral"


    smc_structure: str = "none"


    order_block: str = "none"


    liquidity: str = "none"


    fair_value_gap: bool = False


    premium_discount: str = "none"



    # =========================
    # Future AI Layer
    # =========================

    ai_score: float = 0.0


    liquidity_score: float = 0.0



    # =========================
    # Explanation
    # =========================

    reasons: list[str] = field(
        default_factory=list
    )
