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

    Includes:

    - Market Structure
    - Indicators
    - Momentum
    - Price Action
    - Supply / Demand
    - Candlestick
    - Elliott Wave
    - Harmonic Patterns
    - Al Brooks Price Action
    - Wyckoff
    - Future AI Models
    """



    # =====================
    # Core Analysis
    # =====================

    trend: str


    momentum: str


    indicators: dict[str, Any]



    candles: list[Candle] = field(
        default_factory=list
    )



    # =====================
    # Supply / Demand
    # =====================

    supply_demand: Any = None



    # =====================
    # Main Scores
    # =====================

    trend_score: float = 0.0


    momentum_score: float = 0.0


    structure_score: float = 0.0


    volatility_score: float = 0.0


    price_action_score: float = 0.0



    # =====================
    # Pattern Engines
    # =====================

    candlestick_score: float = 0.0


    elliott_score: float = 0.0


    harmonic_score: float = 0.0


    brooks_score: float = 0.0


    wyckoff_score: float = 0.0



    # =====================
    # Future Expansion
    # =====================

    ai_score: float = 0.0


    smart_money_score: float = 0.0


    liquidity_score: float = 0.0



    # =====================
    # Explanation Layer
    # =====================

    reasons: list[str] = field(
        default_factory=list
    )



# ==================================================
# User Report
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
    """



    trend: str


    structure: str


    score: float


    signal: str


    confidence: float



    reasons: list[str] = field(
        default_factory=list
    )



    indicators: dict[str, Any] = field(
        default_factory=dict
    )
