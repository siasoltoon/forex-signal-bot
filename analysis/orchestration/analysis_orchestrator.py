from __future__ import annotations

from analysis.contracts.context import AnalysisContext
from analysis.contracts.result import AnalysisResult, AnalysisSessionResult
from analysis.registry.analyzer_registry import AnalyzerRegistry


class AnalysisOrchestrator:
    """Runs registered analyzers without coupling to concrete implementations."""

    def __init__(self, registry: AnalyzerRegistry) -> None:
        self.registry = registry

    def analyze(
        self,
        context: AnalysisContext,
        analyzer_ids: tuple[str, ...] | None = None,
    ) -> AnalysisSessionResult:
        analyzers = self.registry.supported(context)
        if analyzer_ids is not None:
            selected = set(analyzer_ids)
            analyzers = tuple(
                analyzer for analyzer in analyzers if analyzer.analyzer_id in selected
            )

        results: list[AnalysisResult] = []
        for analyzer in analyzers:
            results.append(analyzer.analyze(context))

        return self._aggregate(results)

    @staticmethod
    def _aggregate(results: list[AnalysisResult]) -> AnalysisSessionResult:
        if not results:
            return AnalysisSessionResult()

        total_weight = sum(result.weight for result in results)
        if total_weight <= 0:
            return AnalysisSessionResult(results=tuple(results))

        weighted_score = sum(
            result.score * result.weight for result in results
        ) / total_weight
        weighted_confidence = sum(
            result.confidence * result.weight for result in results
        ) / total_weight

        bullish_weight = sum(
            result.weight for result in results if result.direction == "bullish"
        )
        bearish_weight = sum(
            result.weight for result in results if result.direction == "bearish"
        )

        if bullish_weight > bearish_weight and bullish_weight > 0:
            direction = "bullish"
        elif bearish_weight > bullish_weight and bearish_weight > 0:
            direction = "bearish"
        else:
            direction = "neutral"

        disagreement = 1.0 - abs(weighted_score)

        return AnalysisSessionResult(
            results=tuple(results),
            consensus_direction=direction,
            disagreement=max(0.0, min(1.0, disagreement)),
            overall_confidence=max(0.0, min(1.0, weighted_confidence)),
        )
