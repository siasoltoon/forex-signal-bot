from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .evidence import AnalysisEvidence


@dataclass(frozen=True)
class AnalysisResult:
    """Normalized result produced by one analyzer.

    Score is directional and normalized to [-1, 1]. Confidence and weight
    are normalized to [0, 1].
    """

    analyzer_id: str
    direction: str
    score: float
    confidence: float
    weight: float = 1.0
    evidence: Sequence[AnalysisEvidence] = field(default_factory=tuple)
    warnings: Sequence[str] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.analyzer_id:
            raise ValueError("analyzer_id cannot be empty")
        if self.direction not in {"bullish", "bearish", "neutral", "unknown"}:
            raise ValueError("invalid analysis direction")
        if not -1.0 <= self.score <= 1.0:
            raise ValueError("score must be between -1 and 1")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError("weight must be between 0 and 1")


@dataclass(frozen=True)
class AnalysisSessionResult:
    """Aggregate output for one orchestration session."""

    results: Sequence[AnalysisResult] = field(default_factory=tuple)
    consensus_direction: str = "unknown"
    disagreement: float = 0.0
    overall_confidence: float = 0.0
    data_quality: float = 0.0
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.disagreement <= 1.0:
            raise ValueError("disagreement must be between 0 and 1")
        if not 0.0 <= self.overall_confidence <= 1.0:
            raise ValueError("overall_confidence must be between 0 and 1")
        if not 0.0 <= self.data_quality <= 1.0:
            raise ValueError("data_quality must be between 0 and 1")
