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


from analysis.price_action_engine import (
    PriceActionEngine,
)


from analysis.supply_demand_engine import (
    SupplyDemandEngine,
)



class FullAnalysisEngine:
    """
    Complete analysis pipeline.

    Combines:

    - Market Structure
    - Indicators
    - Momentum
    - Price Action
    - Supply / Demand
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


        self.price_action_engine = (
            PriceActionEngine()
        )


        self.supply_demand_engine = (
            SupplyDemandEngine()
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
        # Price Action
        # =========================

        price_action_result = (
            self.price_action_engine.analyze(
                closes
            )
        )



        # =========================
        # Supply Demand
        # =========================

        supply_demand_result = (
            self.supply_demand_engine.analyze(
                closes
            )
        )



        # =========================
        # Build Analysis Result
        # =========================

        analysis_result = AnalysisResult(


            trend=structure.trend,


            momentum=momentum_result.state,


            indicators=indicator_snapshot.values,



            supply_demand=(
                supply_demand_result.zone
            ),



            trend_score=0.0,



            momentum_score=(
                momentum_result.score
            ),



            structure_score=(

                20

                if structure.bos

                else 0

            ),



            volatility_score=0.0,



            price_action_score=(

                price_action_result.score

            ),



            reasons=(

                momentum_result.reasons

                +

                price_action_result.reasons

                +

                [

                    supply_demand_result.reason

                ]

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


            reasons=analysis_result.reasons,


            indicators=indicator_snapshot.values,

        )
