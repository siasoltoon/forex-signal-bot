from __future__ import annotations

from analysis.report import AnalysisReport

from analysis.market_structure import (
    MarketStructureDetector,
)

from analysis.scoring import (
    AnalysisScorer,
)

from analysis.models import (
    AnalysisResult,
)


class FullAnalysisEngine:
    """
    Combined analysis engine.

    Combines:
    - Indicators
    - Market structure
    - Scoring
    """


    def __init__(self) -> None:

        self.structure_detector = (
            MarketStructureDetector()
        )

        self.scorer = AnalysisScorer()



    def analyze(
        self,
        closes: list[float],
    ) -> AnalysisReport:

        structure = (
            self.structure_detector.analyze(
                closes
            )
        )


        analysis_result = AnalysisResult(
            trend=structure.trend,
            momentum="neutral",
            indicators={},
            supply_demand=None,
        )


        score = (
            self.scorer.score(
                analysis_result
            )
        )


        structure_name = (
            "BOS"
            if structure.bos
            else "NORMAL"
        )


        return AnalysisReport(
            trend=structure.trend,
            structure=structure_name,
            score=score.score,
            signal=score.direction,
            confidence=score.confidence,
        )
