from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from .analysis_runtime import AnalysisEvidence, AnalyzerRegistry
from .data_runtime import MarketSnapshot


@dataclass(frozen=True)
class AnalysisContext:
    snapshot: MarketSnapshot
    timeframe: str
    metadata: dict[str, str] | None = None


class AnalyzerPlugin(Protocol):
    name: str
    supported_markets: frozenset[str]
    supported_timeframes: set[str]

    async def analyze(self, snapshot: MarketSnapshot) -> AnalysisEvidence: ...


class PluginAnalyzerRegistry(AnalyzerRegistry):
    def register_plugin(self, plugin: AnalyzerPlugin) -> None:
        self.register(plugin)

    def available(self, market: str, timeframe: str) -> tuple[str, ...]:
        names: list[str] = []
        for name, analyzer in self._items.items():
            markets = getattr(analyzer, "supported_markets", frozenset())
            timeframes = getattr(analyzer, "supported_timeframes", set())
            if (not markets or market in markets) and (not timeframes or timeframe in timeframes):
                names.append(name)
        return tuple(names)


class PluginOrchestrator:
    def __init__(self, registry: PluginAnalyzerRegistry) -> None:
        self.registry = registry

    async def analyze(self, context: AnalysisContext, selected: Sequence[str] | None = None) -> tuple[AnalysisEvidence, ...]:
        names = tuple(selected) if selected is not None else self.registry.available(context.snapshot.request.market.value, context.timeframe)
        analyzers = self.registry.get(names)
        return tuple(await analyzer.analyze(context.snapshot) for analyzer in analyzers)
