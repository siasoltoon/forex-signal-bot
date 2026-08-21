from __future__ import annotations

from analysis.models import (
    AnalysisScore,
    SignalComponent,
)


class AnalysisScorer:
    """
    Convert technical analysis results
    into a normalized trading score.
    """

    def score(
        self,
        analysis_result,
    ) -> AnalysisScore:
        """
        Calculate final analysis score.
        """

        components = []

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
                reason="RSI indicates oversold condition.",
            )


        if momentum == "overbought":
            return SignalComponent(
                name="momentum",
                score=-20,
                reason="RSI indicates overbought condition.",
            )


        return SignalComponent(
            name="momentum",
            score=0,
            reason="Neutral momentum.",
        )


    @staticmethod
    def _direction(
        score: float,
    ) -> str:

        if score >= 20:
            return "BUY"


        if score <= -20:
            return "SELL"


        return "NEUTRAL"
