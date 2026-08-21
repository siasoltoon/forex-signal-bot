from __future__ import annotations

from analysis.models import (
    SignalComponent,
    AnalysisScore,
    AnalysisResult,
)


class AnalysisScorer:
    """
    Calculate final technical analysis score.
    """

    def score(
        self,
        analysis_result: AnalysisResult,
    ) -> AnalysisScore:

        components: list[SignalComponent] = []


        # Trend

        components.append(
            self._score_trend(
                analysis_result.trend
            )
        )


        # Momentum

        components.append(
            self._score_momentum(
                analysis_result
            )
        )


        # Supply / Demand

        supply_demand = getattr(
            analysis_result,
            "supply_demand",
            None,
        )

        if supply_demand:

            components.append(
                self._score_supply_demand(
                    supply_demand
                )
            )



        total_score = sum(
            component.score
            for component in components
        )



        total_score = max(
            -100,
            min(
                100,
                total_score,
            ),
        )



        return AnalysisScore(
            score=float(total_score),

            direction=self._direction(
                total_score
            ),

            confidence=abs(
                total_score
            ) / 100,
        )



    @staticmethod
    def _score_trend(
        trend: str,
    ) -> SignalComponent:


        if trend == "bullish":

            return SignalComponent(
                name="trend",
                score=30,
                reason="Bullish trend detected.",
            )


        if trend == "bearish":

            return SignalComponent(
                name="trend",
                score=-30,
                reason="Bearish trend detected.",
            )


        return SignalComponent(
            name="trend",
            score=0,
            reason="No clear trend.",
        )



    @staticmethod
    def _score_momentum(
        analysis_result: AnalysisResult,
    ) -> SignalComponent:


        # Use advanced momentum score

        if (
            analysis_result.momentum_score
            != 0
        ):

            return SignalComponent(
                name="momentum",

                score=analysis_result.momentum_score,

                reason=(
                    ", ".join(
                        analysis_result.momentum_reasons
                        or []
                    )
                    or
                    "Momentum analysis."
                ),
            )



        # Backward compatibility

        momentum = (
            analysis_result.momentum
        )


        if momentum == "oversold":

            return SignalComponent(
                name="momentum",
                score=20,
                reason="Market is oversold.",
            )


        if momentum == "overbought":

            return SignalComponent(
                name="momentum",
                score=-20,
                reason="Market is overbought.",
            )



        return SignalComponent(
            name="momentum",
            score=0,
            reason="Neutral momentum.",
        )



    @staticmethod
    def _score_supply_demand(
        supply_demand,
    ) -> SignalComponent:


        if supply_demand == "demand":

            return SignalComponent(
                name="supply_demand",
                score=20,
                reason="Demand zone detected.",
            )


        if supply_demand == "supply":

            return SignalComponent(
                name="supply_demand",
                score=-20,
                reason="Supply zone detected.",
            )


        return SignalComponent(
            name="supply_demand",
            score=0,
            reason="No supply/demand signal.",
        )



    @staticmethod
    def _direction(
        score: float,
    ) -> str:


        if score > 0:

            return "BUY"


        if score < 0:

            return "SELL"


        return "NEUTRAL"
