from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from analysis.contracts import AnalysisContext, AnalysisOutput, Analyzer
from analysis.registry import AnalyzerRegistry
from analysis.selection import AnalysisSelection, validate_selection


@dataclass(frozen=True, slots=True)
class PluginRun:
    requested: tuple[str, ...]
    executed: tuple[str, ...]
    skipped: tuple[str, ...]
    results: tuple[AnalysisOutput, ...]


class AnalysisPluginRuntime:
    """Executes only explicitly selected, registered analyzers."""

    def __init__(self, registry: AnalyzerRegistry) -> None:
        self.registry = registry

    def run(self, context: AnalysisContext, selection: AnalysisSelection) -> PluginRun:
        available = set(self.registry.names())
        validate_selection(selection, available)
        requested = tuple(dict.fromkeys(selection.effective_styles()))
        results: list[AnalysisOutput] = []
        skipped: list[str] = []
        for name in requested:
            try:
                analyzer: Analyzer = self.registry.create(name)
            except (KeyError, TypeError):
                skipped.append(name)
                continue
            try:
                results.append(analyzer.analyze(context))
            except Exception as exc:  # plugin isolation: one analyzer must not crash the run
                results.append(AnalysisOutput(analyzer=name, success=False, error=str(exc)))
        return PluginRun(requested, tuple(r.analyzer for r in results), tuple(skipped), tuple(results))
