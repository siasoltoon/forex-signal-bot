from __future__ import annotations

from analysis.models import (
    AnalysisScore,
    AnalysisResult,
    SignalComponent,
)


class AnalysisScorer:
    """
    Professional scoring engine.

    Combines:
    - Trend
    - Momentum
    - Supply/Demand
    - Market Structure
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


        if analysis_result.supply_demand:

            components.append(
                self._score_supply_demand(
                    analysis_result.supply_demand
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
            )
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
                reason="Price above moving average.",
            )


        if trend == "bearish":
            return SignalComponent(
                name="trend",
                score=-30,
                reason="Price below moving average.",
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
                reason="RSI oversold.",
            )


        if momentum == "overbought":
            return SignalComponent(
                name="momentum",
                score=-20,
                reason="RSI overbought.",
            )


        return SignalComponent(
            name="momentum",
            score=0,
            reason="Neutral momentum.",
        )



    @staticmethod
    def _score_supply_demand(
        zone,
    ) -> SignalComponent:


        if getattr(
            zone,
            "type",
            None
        ) == "demand":

            return SignalComponent(
                name="supply_demand",
                score=25,
                reason="Price inside demand zone.",
            )


        if getattr(
            zone,
            "type",
            None
        ) == "supply":

            return SignalComponent(
                name="supply_demand",
                score=-25,
                reason="Price inside supply zone.",
            )


        return SignalComponent(
            name="supply_demand",
            score=0,
            reason="No active zone.",
        )



    @staticmethod
    def _direction(
        score: float,
    ) -> str:

        if score >= 50:
            return "BUY"


        if score <= -50:
            return "SELL"


        return "HOLD"
