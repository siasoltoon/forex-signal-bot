"""Analysis integration bridge.

Keeps the analysis layer decoupled from providers and runtime services.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AnalysisContext:
    """Normalized context passed into analyzers."""

    symbol: str
    timeframe: str
    candles: list[Any] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AnalysisResult:
    """Common explainable analyzer output contract."""

    analyzer: str
    signal: str
    confidence: float
    explanation: str
    metadata: dict[str, Any] = field(default_factory=dict)


class AnalysisBridge:
    """Small compatibility layer for connecting analyzers safely."""

    def build_context(self, symbol: str, timeframe: str, candles: list[Any], **metadata: Any) -> AnalysisContext:
        return AnalysisContext(
            symbol=symbol,
            timeframe=timeframe,
            candles=candles,
            metadata=metadata,
        )

    def normalize_result(self, result: AnalysisResult) -> AnalysisResult:
        result.confidence = max(0.0, min(1.0, float(result.confidence)))
        return result
