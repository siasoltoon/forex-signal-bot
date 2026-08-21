from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any



@dataclass(
    frozen=True
)
class SignalComponent:
    """
    Single scoring component.

    Example:
    Trend = +30
    Momentum = +20
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

    Contains outputs from:
    - Market structure
    - Indicators
    - Momentum
    - Supply/Demand
    - Future price action engines
    """


    trend: str


    momentum: str


    indicators: dict[str, Any]


    supply_demand: Any = None



    # Advanced scoring fields

    trend_score: float = 0.0


    momentum_score: float = 0.0


    structure_score: float = 0.0


    volatility_score: float = 0.0



    # Explanation layer

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



    # Extended information

    reasons: list[str] = field(
        default_factory=list
    )

    indicators: dict[str, Any] = field(
        default_factory=dict
    )
