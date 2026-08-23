from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .analysis_runtime import AnalysisOrchestrator, AnalyzerRegistry
from .data_runtime import MarketRequest, ProviderManager
from .intelligence import AdvancedFusion, IntelligenceDecision


@dataclass(frozen=True)
class PipelineRequest:
    requests: tuple[MarketRequest, ...]
    analyzer_names: tuple[str, ...] | None = None


class ProductionAnalysisPipeline:
    """End-to-end runtime: provider -> validation -> MTF analysis -> fusion."""

    def __init__(self, providers: ProviderManager, analyzers: AnalyzerRegistry, fusion: AdvancedFusion | None = None) -> None:
        self.providers = providers
        self.orchestrator = AnalysisOrchestrator(analyzers)
        self.fusion = fusion or AdvancedFusion()

    async def analyze(self, request: PipelineRequest) -> IntelligenceDecision:
        if not request.requests:
            raise ValueError("at least one timeframe request is required")
        snapshots = []
        for item in request.requests:
            snapshot = await self.providers.snapshot(item)
            if not snapshot.quality.valid:
                raise RuntimeError("NO TRADE: invalid market data")
            snapshots.append(snapshot)
        mtf = await self.orchestrator.run(tuple(snapshots), request.analyzer_names)
        quality = min(snapshot.quality.score for snapshot in snapshots)
        return self.fusion.fuse(mtf, quality)
