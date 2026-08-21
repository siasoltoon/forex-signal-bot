from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from analysis.candle import Candle



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



@dataclass(
    frozen=True
)
class AnalysisResult:
    """
    Complete technical analysis state.

    Includes:

    - Market Structure
    - OHLC Candles
    - Indicators
    - Momentum
    - Price Action
    - Supply / Demand
    - Candlestick Patterns
    - Elliott Wave
    - Harmonic Patterns
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
    # Scoring Engines
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


    wyckoff_score: float = 0.0



    # =====================
    # Explanation Layer
    # =====================

    reasons: list[str] = field(
        default_factory=list
    )



@dataclass(
    frozen=True
)
class AnalysisReport:
    """
    Final user-facing analysis report.
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
