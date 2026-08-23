from __future__ import annotations

from dataclasses import asdict
from typing import Any

from analysis.contracts import AnalysisContext, AnalysisOutput
from analysis.engine import AnalysisEngine


class LegacyAnalysisEngineAdapter:
    """Compatibility adapter that exposes the existing AnalysisEngine as an Analyzer."""

    name = "technical"

    def __init__(self, engine: AnalysisEngine | None = None) -> None:
        self.engine = engine or AnalysisEngine()

    def analyze(self, context: AnalysisContext) -> AnalysisOutput:
        closes = context.data
        if not isinstance(closes, list):
            raise TypeError("Legacy technical analyzer requires context.data to be a list of closes")
        result = self.engine.analyze(closes)
        return AnalysisOutput(
            analyzer=self.name,
            success=True,
            values=asdict(result),
        )


def register_legacy_analyzers(registry: Any) -> None:
    """Register currently safe legacy analyzers without changing their implementation."""
    registry.register(LegacyAnalysisEngineAdapter.name, LegacyAnalysisEngineAdapter)
