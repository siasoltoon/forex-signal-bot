from __future__ import annotations


from analysis.models import (
    AnalysisResult,
)


from analysis.report import (
    AnalysisReport,
)


from analysis.candle import (
    Candle,
)


from analysis.market_structure import (
    MarketStructureDetector,
)


from analysis.decision_engine import (
    DecisionEngine,
)


from analysis.confidence_engine import (
    ConfidenceEngine,
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


from analysis.candlestick_engine import (
    CandlestickEngine,
)


from analysis.elliott_engine import (
    ElliottEngine,
)


from analysis.harmonic_engine import (
    HarmonicEngine,
)


from analysis.brooks_engine import (
    BrooksEngine,
)


from analysis.wyckoff_engine import (
    WyckoffEngine,
)


from analysis.smc_engine import (
    SMCEngine,
)



class FullAnalysisEngine:
    """
    Complete analysis pipeline.

    Modules:

    - Market Structure
    - Indicators
    - Momentum
    - Price Action
    - Supply Demand
    - Candlestick
    - Elliott Wave
    - Harmonic
    - Al Brooks
    - Wyckoff
    - Smart Money Concepts
    - Decision Engine
    - Confidence Engine
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


        self.candlestick_engine = (
            CandlestickEngine()
        )


        self.elliott_engine = (
            ElliottEngine()
        )


        self.harmonic_engine = (
            HarmonicEngine()
        )


        self.brooks_engine = (
            BrooksEngine()
        )


        self.wyckoff_engine = (
            WyckoffEngine()
        )


        self.smc_engine = (
            SMCEngine()
        )



        self.decision_engine = (
            DecisionEngine()
        )


        self.confidence_engine = (
            ConfidenceEngine()
        )



    # ==================================================
    # Safe Engine Runner
    # ==================================================

    @staticmethod
    def _safe_run(
        engine,
        method_name: str,
        data,
        default=None,
    ):

        try:

            method = getattr(
                engine,
                method_name
            )

            return method(data)


        except Exception:

            return default



    # ==================================================
    # Main Analysis
    # ==================================================

    def analyze(
        self,
        candles: list[Candle] | list[float],
    ) -> AnalysisReport:


        if not candles:

            raise ValueError(
                "Input candles cannot be empty."
            )



        # ==================================================
        # Normalize Input
        # ==================================================

        if isinstance(
            candles[0],
            Candle
        ):


            candle_data = candles


            closes = [

                candle.close

                for candle in candle_data

            ]


        else:


            closes = [

                float(price)

                for price in candles

            ]


            candle_data = [

                Candle(

                    open=price,

                    high=price,

                    low=price,

                    close=price,

                    volume=0.0,

                )

                for price in closes

            ]



        # ==================================================
        # Core Engines
        # ==================================================


        structure = (
            self.structure_detector.analyze(
                closes
            )
        )


        indicator_snapshot = (
            self.indicator_engine.calculate(
                closes
            )
        )


        momentum_result = (
            self.momentum_engine.analyze(
                indicator_snapshot.values
            )
        )


        price_action_result = (
            self.price_action_engine.analyze(
                closes
            )
        )


        supply_demand_result = (
            self.supply_demand_engine.analyze(
                closes
            )
        )


        candlestick_result = (
            self.candlestick_engine.analyze(
                candle_data
            )
        )



        # ==================================================
        # Advanced Engines
        # ==================================================


        elliott_result = (
            self.elliott_engine.analyze(
                closes
            )
        )


        harmonic_result = (
            self.harmonic_engine.analyze(
                closes
            )
        )


        brooks_result = (
            self.brooks_engine.analyze(
                closes
            )
        )


        wyckoff_result = (
            self.wyckoff_engine.analyze(
                closes
            )
        )


        smc_result = (
            self.smc_engine.analyze(
                closes
            )
        )


        
        # ==================================================
        # Build Analysis Result
        # ==================================================

        analysis_result = AnalysisResult(

            trend=structure.trend,


            momentum=momentum_result.state,


            indicators=indicator_snapshot.values,


            candles=candle_data,


            supply_demand=(

                supply_demand_result.zone

            ),



            trend_score=(

                20

                if structure.trend == "bullish"

                else -20

                if structure.trend == "bearish"

                else 0

            ),



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



            candlestick_score=(

                candlestick_result.score

            ),



            elliott_score=(

                elliott_result.score

            ),



            harmonic_score=(

                harmonic_result.score

            ),



            brooks_score=(

                brooks_result.score

            ),



            wyckoff_score=(

                wyckoff_result.score

            ),



            smart_money_score=(

                smc_result.score

            ),



            smc_bias=(

                smc_result.bias

            ),



            smc_structure=(

                smc_result.structure

            ),



            order_block=(

                smc_result.order_block

            ),



            liquidity=(

                smc_result.liquidity

            ),



            fair_value_gap=(

                smc_result.fair_value_gap

            ),



            premium_discount=(

                smc_result.premium_discount

            ),



            reasons=(

                momentum_result.reasons

                +

                price_action_result.reasons

                +

                [

                    supply_demand_result.reason,

                    candlestick_result.reason,

                    elliott_result.reason,

                    harmonic_result.reason,

                    brooks_result.reason,

                    wyckoff_result.reason,

                    smc_result.reason,

                ]

            ),

        )



        # ==================================================
        # Decision Layer
        # ==================================================

        decision = (

            self.decision_engine.decide(

                analysis_result

            )

        )



        # ==================================================
        # Confidence Layer
        # ==================================================

        confidence_result = (

            self.confidence_engine.evaluate(

                analysis_result

            )

        )



        structure_name = (

            "BOS"

            if structure.bos

            else

            "NORMAL"

        )



        # ==================================================
        # Final Report
        # ==================================================

        return AnalysisReport(


            trend=structure.trend,


            structure=structure_name,


            score=decision.score,


            signal=decision.signal,


            confidence=confidence_result.confidence,



            smc_bias=(

                smc_result.bias

            ),



            smc_structure=(

                smc_result.structure

            ),



            order_block=(

                smc_result.order_block

            ),



            liquidity=(

                smc_result.liquidity

            ),



            fair_value_gap=(

                smc_result.fair_value_gap

            ),



            premium_discount=(

                smc_result.premium_discount

            ),



            reasons=(

                analysis_result.reasons

                +

                decision.reasons

                +

                confidence_result.warnings

            ),



            indicators=(

                indicator_snapshot.values

            ),

        )
