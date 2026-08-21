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


from analysis.indicator_engine import (
    IndicatorEngine,
)


from analysis.momentum_engine import (
    MomentumEngine,
)



class FullAnalysisEngine:
    """
    Combined analysis engine.

    Combines:
    - Indicators
    - Market structure
    - Momentum analysis
    - Scoring
    """


    def __init__(self) -> None:

        self.structure_detector = (
            MarketStructureDetector()
        )


        self.indicator_engine = (
            IndicatorEngine()
        )


        self.momentum_engine = (
            MomentumEngine()
        )


        self.scorer = AnalysisScorer()



    def analyze(
        self,
        closes: list[float],
    ) -> AnalysisReport:


        # =========================
        # Market Structure
        # =========================

        structure = (
            self.structure_detector.analyze(
                closes
            )
        )



        # =========================
        # Indicators
        # =========================

        indicator_snapshot = (
            self.indicator_engine.calculate(
                closes
            )
        )



        # =========================
        # Momentum
        # =========================

        momentum_result = (
            self.momentum_engine.analyze(
                indicator_snapshot.values
            )
        )



        # =========================
        # Build Analysis Result
        # =========================

        analysis_result = AnalysisResult(

            trend=structure.trend,


            momentum=momentum_result.state,


            indicators=indicator_snapshot.values,


            supply_demand=None,


            # Advanced scoring data

            momentum_score=(
                momentum_result.score
            ),


            structure_score=(
                20
                if structure.bos
                else 0
            ),


            reasons=(
                momentum_result.reasons
            ),
        )



        # =========================
        # Final Score
        # =========================

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


            reasons=(
                analysis_result.reasons
            ),


            indicators=(
                indicator_snapshot.values
            ),
        )
