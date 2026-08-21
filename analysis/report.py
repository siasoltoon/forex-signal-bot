from __future__ import annotations

from dataclasses import dataclass


@dataclass(
    frozen=True
)
class AnalysisReport:
    """
    Final combined analysis report.
    """

    trend: str

    structure: str

    score: float

    signal: str

    confidence: float
