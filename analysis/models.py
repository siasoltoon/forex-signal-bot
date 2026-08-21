from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(
    frozen=True
)
class SignalComponent:
    """
    Single scoring component.

    Example:
    Trend score = +30
    Momentum score = -10
    """

    name: str
    score: float
    reason: str


@dataclass(
    frozen=True
)
class AnalysisScore:
    """
    Final analysis score result.
    """

    score: float
    direction: str
    confidence: float


@dataclass(
    frozen=True
)
class AnalysisReport:
    """
    Complete analysis report.
    """

    signal: str
    score: AnalysisScore
    components: list[SignalComponent]


@dataclass(
    frozen=True
)
class AnalysisResult:
    """
    Technical analysis result.
    """

    trend: str

    momentum: str

    indicators: dict[str, Any]

    supply_demand: Any = None
