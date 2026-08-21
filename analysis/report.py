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
    - Final score
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



    # Explanation layer

    reasons: list[str] = field(
        default_factory=list
    )



    # Indicator snapshot

    indicators: dict[str, Any] = field(
        default_factory=dict
    )
