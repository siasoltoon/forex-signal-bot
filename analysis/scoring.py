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

        components.append(
            self._score_trend(
                analysis_result.trend
            )
        )

        components.append(
            self._score_momentum(
                analysis_result.momentum
            )
        )

        # Supply / Demand (optional)
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
                reason="Price is above moving average.",
            )

        if trend == "bearish":
            return SignalComponent(
                name="trend",
                score=-30,
                reason="Price is below moving average.",
            )


        return SignalComponent(
            name="trend",
            score=0,
            reason="No clear trend.",
        )


    @staticmethod
    def _score_momentum(
        momentum: str,
    ) -> SignalComponent:

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
