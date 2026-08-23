from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class AnalysisContext:
    """Immutable input envelope shared by analyzers."""

    symbol: str
    timeframe: str
    data: Any
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AnalysisOutput:
    """Normalized analyzer output."""

    analyzer: str
    success: bool
    values: Mapping[str, Any] = field(default_factory=dict)
    confidence: float | None = None
    warnings: tuple[str, ...] = ()
    error: str | None = None


@dataclass(frozen=True)
class AnalysisRun:
    """Complete result envelope for an analysis orchestration pass."""

    context: AnalysisContext
    results: tuple[AnalysisOutput, ...]

    @property
    def successful(self) -> tuple[AnalysisOutput, ...]:
        return tuple(result for result in self.results if result.success)

    @property
    def failed(self) -> tuple[AnalysisOutput, ...]:
        return tuple(result for result in self.results if not result.success)


class Analyzer(Protocol):
    """Contract implemented by every analysis module."""

    name: str

    def analyze(self, context: AnalysisContext) -> AnalysisOutput:
        ...


class AnalyzerFactory(Protocol):
    def __call__(self) -> Analyzer:
        ...
