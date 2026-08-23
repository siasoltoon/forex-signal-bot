from __future__ import annotations

from analysis.contracts.analyzer import Analyzer


class AnalyzerRegistry:
    """Explicit registry for analyzer plugins."""

    def __init__(self) -> None:
        self._analyzers: dict[str, Analyzer] = {}

    def register(self, analyzer: Analyzer) -> None:
        analyzer_id = analyzer.analyzer_id
        if not analyzer_id:
            raise ValueError("analyzer_id cannot be empty")
        if analyzer_id in self._analyzers:
            raise ValueError(f"analyzer already registered: {analyzer_id}")
        self._analyzers[analyzer_id] = analyzer

    def unregister(self, analyzer_id: str) -> None:
        self._analyzers.pop(analyzer_id, None)

    def get(self, analyzer_id: str) -> Analyzer:
        try:
            return self._analyzers[analyzer_id]
        except KeyError as exc:
            raise KeyError(f"unknown analyzer: {analyzer_id}") from exc

    def all(self) -> tuple[Analyzer, ...]:
        return tuple(self._analyzers.values())

    def supported(self, context) -> tuple[Analyzer, ...]:
        return tuple(
            analyzer
            for analyzer in self._analyzers.values()
            if analyzer.supports(context)
        )
