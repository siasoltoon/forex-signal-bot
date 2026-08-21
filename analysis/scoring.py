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
    - Candlestick
    - Elliott Wave
    - Harmonic Pattern
    - Brooks Price Action
    - Wyckoff
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


        components.append(
            self._score_candlestick(
                analysis_result
            )
        )


        components.append(
            self._score_elliott(
                analysis_result
            )
        )


        components.append(
            self._score_harmonic(
                analysis_result
            )
        )


        components.append(
            self._score_brooks(
                analysis_result
            )
        )


        components.append(
            self._score_wyckoff(
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


        score = getattr(
            result,
            "trend_score",
            0.0,
        )


        if score != 0:

            return SignalComponent(
                name="trend",
                score=score,
                reason="Trend engine score.",
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
    # Structure
    # =========================


    @staticmethod
    def _score_structure(
        result: AnalysisResult,
    ) -> SignalComponent:


        return SignalComponent(
            name="structure",
            score=getattr(
                result,
                "structure_score",
                0.0,
            ),
            reason="Market structure score.",
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


        return SignalComponent(
            name="volatility",
            score=getattr(
                result,
                "volatility_score",
                0.0,
            ),
            reason="Volatility engine score.",
        )



    # =========================
    # Supply Demand
    # =========================


    @staticmethod
    def _score_supply_demand(
        result: AnalysisResult,
    ) -> SignalComponent:


        zone = str(
            result.supply_demand
        ).lower()


        if zone == "demand":

            return SignalComponent(
                name="supply_demand",
                score=15,
                reason="Demand zone detected.",
            )


        if zone == "supply":

            return SignalComponent(
                name="supply_demand",
                score=-15,
                reason="Supply zone detected.",
            )


        return SignalComponent(
            name="supply_demand",
            score=0,
            reason="Neutral supply demand.",
        )



    # =========================
    # Price Action
    # =========================


    @staticmethod
    def _score_price_action(
        result: AnalysisResult,
    ) -> SignalComponent:


        return SignalComponent(
            name="price_action",
            score=getattr(
                result,
                "price_action_score",
                0.0,
            ),
            reason="Price action score.",
        )



    # =========================
    # Candlestick
    # =========================


    @staticmethod
    def _score_candlestick(
        result: AnalysisResult,
    ) -> SignalComponent:


        return SignalComponent(
            name="candlestick",
            score=getattr(
                result,
                "candlestick_score",
                0.0,
            ),
            reason="Candlestick pattern score.",
        )



    # =========================
    # Elliott
    # =========================


    @staticmethod
    def _score_elliott(
        result: AnalysisResult,
    ) -> SignalComponent:


        return SignalComponent(
            name="elliott",
            score=getattr(
                result,
                "elliott_score",
                0.0,
            ),
            reason="Elliott wave score.",
        )



    # =========================
    # Harmonic
    # =========================


    @staticmethod
    def _score_harmonic(
        result: AnalysisResult,
    ) -> SignalComponent:


        return SignalComponent(
            name="harmonic",
            score=getattr(
                result,
                "harmonic_score",
                0.0,
            ),
            reason="Harmonic pattern score.",
        )



    # =========================
    # Brooks Price Action
    # =========================


    @staticmethod
    def _score_brooks(
        result: AnalysisResult,
    ) -> SignalComponent:


        brooks_score = getattr(
            result,
            "brooks_score",
            0.0,
        )


        if brooks_score != 0:

            return SignalComponent(
                name="brooks",
                score=brooks_score,
                reason="Al Brooks price action score.",
            )


        return SignalComponent(
            name="brooks",
            score=0.0,
            reason="No Brooks pattern detected.",
        )



    # =========================
    # Wyckoff
    # =========================


    @staticmethod
    def _score_wyckoff(
        result: AnalysisResult,
    ) -> SignalComponent:


        return SignalComponent(
            name="wyckoff",
            score=getattr(
                result,
                "wyckoff_score",
                0.0,
            ),
            reason="Wyckoff analysis score.",
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
