from __future__ import annotations


from analysis.models import (
    SignalComponent,
    AnalysisScore,
    AnalysisResult,
)



class AnalysisScorer:
    """
    Advanced multi-factor scoring engine.

    Factors:
    - Trend
    - Market Structure
    - Momentum
    - Volatility
    - Supply/Demand
    - Price Action
    """



    def score(
        self,
        analysis_result: AnalysisResult,
    ) -> AnalysisScore:


        components: list[SignalComponent] = []


        components.append(
            self._score_trend(
                analysis_result
            )
        )


        components.append(
            self._score_structure(
                analysis_result
            )
        )


        components.append(
            self._score_momentum(
                analysis_result
            )
        )


        components.append(
            self._score_volatility(
                analysis_result
            )
        )


        if getattr(
            analysis_result,
            "supply_demand",
            None,
        ):

            components.append(
                self._score_supply_demand(
                    analysis_result
                )
            )


        components.append(
            self._score_price_action(
                analysis_result
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

            confidence=(
                abs(total_score)
                /
                100
            ),

            components=components,
        )



    # =========================
    # Trend
    # =========================


    @staticmethod
    def _score_trend(
        result: AnalysisResult,
    ) -> SignalComponent:


        trend_score = getattr(
            result,
            "trend_score",
            0.0,
        )


        if trend_score != 0:

            return SignalComponent(
                name="trend",
                score=trend_score,
                reason="Trend score from analysis engine.",
            )


        if result.trend == "bullish":

            return SignalComponent(
                name="trend",
                score=30,
                reason="Bullish trend detected.",
            )


        if result.trend == "bearish":

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



    # =========================
    # Market Structure
    # =========================


    @staticmethod
    def _score_structure(
        result: AnalysisResult,
    ) -> SignalComponent:


        structure_score = getattr(
            result,
            "structure_score",
            0.0,
        )


        if structure_score > 0:

            return SignalComponent(
                name="structure",
                score=structure_score,
                reason="Bullish market structure.",
            )


        if structure_score < 0:

            return SignalComponent(
                name="structure",
                score=structure_score,
                reason="Bearish market structure.",
            )


        return SignalComponent(
            name="structure",
            score=0,
            reason="No structure signal.",
        )



    # =========================
    # Momentum
    # =========================


    @staticmethod
    def _score_momentum(
        result: AnalysisResult,
    ) -> SignalComponent:


        momentum_score = getattr(
            result,
            "momentum_score",
            0.0,
        )


        if momentum_score != 0:

            return SignalComponent(
                name="momentum",
                score=momentum_score,
                reason="Momentum engine score.",
            )


        if result.momentum == "oversold":

            return SignalComponent(
                name="momentum",
                score=20,
                reason="Market is oversold.",
            )


        if result.momentum == "overbought":

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



    # =========================
    # Volatility
    # =========================


    @staticmethod
    def _score_volatility(
        result: AnalysisResult,
    ) -> SignalComponent:


        volatility_score = getattr(
            result,
            "volatility_score",
            0.0,
        )


        if volatility_score != 0:

            return SignalComponent(
                name="volatility",
                score=volatility_score,
                reason="Volatility analysis score.",
            )


        return SignalComponent(
            name="volatility",
            score=0,
            reason="No volatility signal.",
        )



    # =========================
    # Supply Demand
    # =========================


    @staticmethod
    def _score_supply_demand(
        result: AnalysisResult,
    ) -> SignalComponent:


        if result.supply_demand == "demand":

            return SignalComponent(
                name="supply_demand",
                score=15,
                reason="Demand zone detected.",
            )


        if result.supply_demand == "supply":

            return SignalComponent(
                name="supply_demand",
                score=-15,
                reason="Supply zone detected.",
            )


        return SignalComponent(
            name="supply_demand",
            score=0,
            reason="No supply/demand signal.",
        )



    # =========================
    # Price Action
    # =========================


    @staticmethod
    def _score_price_action(
        result: AnalysisResult,
    ) -> SignalComponent:


        price_action_score = getattr(
            result,
            "price_action_score",
            0.0,
        )


        if price_action_score != 0:

            return SignalComponent(
                name="price_action",
                score=price_action_score,
                reason="Price action score.",
            )


        return SignalComponent(
            name="price_action",
            score=0,
            reason="No price action signal.",
        )



    # =========================
    # Direction
    # =========================


    @staticmethod
    def _direction(
        score: float,
    ) -> str:


        if score > 0:
            return "BUY"


        if score < 0:
            return "SELL"


        return "NEUTRAL"
