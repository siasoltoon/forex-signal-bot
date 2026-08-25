"""Analyzer registry infrastructure for the intelligent analysis system.

Keeps analyzer discovery and execution decoupled from individual analysis modules.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type


@dataclass
class AnalyzerMetadata:
    name: str
    category: str
    enabled: bool = True


class AnalyzerRegistry:
    def __init__(self):
        self._analyzers: Dict[str, Any] = {}
        self._metadata: Dict[str, AnalyzerMetadata] = {}

    def register(self, name: str, analyzer: Any, category: str = "general") -> None:
        self._analyzers[name] = analyzer
        self._metadata[name] = AnalyzerMetadata(
            name=name,
            category=category,
        )

    def get(self, name: str) -> Optional[Any]:
        return self._analyzers.get(name)

    def list_enabled(self) -> List[AnalyzerMetadata]:
        return [m for m in self._metadata.values() if m.enabled]

    def execute(self, name: str, context: Any) -> Any:
        analyzer = self.get(name)
        if analyzer is None:
            raise ValueError(f"Analyzer not registered: {name}")
        return analyzer.analyze(context)


registry = AnalyzerRegistry()
