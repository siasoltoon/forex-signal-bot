from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, Sequence

from .data_runtime import MarketSnapshot


@dataclass(frozen=True)
class AnalysisEvidence:
    analyzer: str
    direction: str
    strength: float
    confidence: float
    quality: float
    timeframe: str
    details: dict[str, Any]


class Analyzer(Protocol):
    name: str
    supported_timeframes: set[str]
    async def analyze(self, snapshot: MarketSnapshot) -> AnalysisEvidence: ...


class AnalyzerRegistry:
    def __init__(self, analyzers: Sequence[Analyzer] = ()) -> None:
        self._items: dict[str, Analyzer] = {item.name: item for item in analyzers}

    def register(self, analyzer: Analyzer) -> None:
        if analyzer.name in self._items:
            raise ValueError(f"analyzer already registered: {analyzer.name}")
        self._items[analyzer.name] = analyzer

    def get(self, names: Sequence[str] | None = None) -> tuple[Analyzer, ...]:
        if names is None:
            return tuple(self._items.values())
        return tuple(self._items[name] for name in names if name in self._items)


@dataclass(frozen=True)
class MultiTimeframeEvidence:
    evidence: tuple[AnalysisEvidence, ...]
    alignment_score: float
    conflicts: tuple[str, ...]


class AnalysisOrchestrator:
    def __init__(self, registry: AnalyzerRegistry) -> None:
        self.registry = registry

    async def run(self, snapshots: Sequence[MarketSnapshot], analyzer_names: Sequence[str] | None = None) -> MultiTimeframeEvidence:
        by_tf = {snapshot.request.timeframe: snapshot for snapshot in snapshots}
        results: list[AnalysisEvidence] = []
        for analyzer in self.registry.get(analyzer_names):
            for timeframe in analyzer.supported_timeframes:
                snapshot = by_tf.get(timeframe)
                if snapshot:
                    results.append(await analyzer.analyze(snapshot))
        directions = {item.direction for item in results if item.direction in {"BUY", "SELL"}}
        conflicts = ("multi_timeframe_direction_conflict",) if len(directions) > 1 else ()
        alignment = 100.0 if not conflicts else 50.0
        return MultiTimeframeEvidence(tuple(results), alignment, conflicts)
