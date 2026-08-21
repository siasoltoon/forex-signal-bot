from __future__ import annotations

from dataclasses import dataclass



# ==================================================
# Risk Result
# ==================================================

@dataclass(
    frozen=True
)
class RiskResult:
    """
    Trade risk calculation output.
    """

    entry_price: float | None

    stop_loss: float | None

    take_profit: float | None

    risk_reward: float | None

    risk_level: str

    reason: str



# ==================================================
# Risk Engine
# ==================================================

class RiskEngine:
    """
    Advanced trade risk management engine.

    Features:

    - Entry calculation
    - ATR based Stop Loss
    - ATR based Take Profit
    - Risk Reward calculation
    - Dynamic risk level
    - Confidence aware risk
    - Score aware risk
    """



    def __init__(
        self,
        risk_reward_target: float = 2.0,
        atr_multiplier: float = 1.5,
    ) -> None:


        self.risk_reward_target = (
            risk_reward_target
        )


        self.atr_multiplier = (
            atr_multiplier
        )



    # ==================================================
    # Risk Level
    # ==================================================

    @staticmethod
    def _calculate_risk_level(
        confidence: float,
        score: float,
    ) -> str:
        """
        Determines risk level from
        confidence and decision score.
        """


        if (

            confidence >= 0.80

            and

            abs(score) >= 60

        ):

            return "LOW"



        elif (

            confidence >= 0.50

        ):

            return "MEDIUM"



        else:

            return "HIGH"




    # ==================================================
    # Risk Distance
    # ==================================================

    def _calculate_risk_distance(
        self,
        price: float,
        atr: float | None = None,
        risk_distance: float | None = None,
    ) -> float:
        """
        Calculates stop distance.

        Priority:

        1. Manual risk distance
        2. ATR based distance
        3. Percentage fallback
        """



        if risk_distance is not None:

            return abs(
                risk_distance
            )



        if atr is not None and atr > 0:

            return (

                atr

                *

                self.atr_multiplier

            )



        return (

            price

            *

            0.01

        )



    # ==================================================
    # BUY Setup
    # ==================================================

    def _buy_setup(
        self,
        price: float,
        risk_distance: float,
        risk_level: str,
    ) -> RiskResult:


        entry = price


        stop_loss = (

            price

            -

            risk_distance

        )


        take_profit = (

            price

            +

            (

                risk_distance

                *

                self.risk_reward_target

            )

        )


        return RiskResult(

            entry_price=round(
                entry,
                5
            ),


            stop_loss=round(
                stop_loss,
                5
            ),


            take_profit=round(
                take_profit,
                5
            ),


            risk_reward=self.risk_reward_target,


            risk_level=risk_level,


            reason=(

                "Bullish setup risk calculated using ATR and confidence"

            ),

        )


    
    # ==================================================
    # SELL Setup
    # ==================================================

    def _sell_setup(
        self,
        price: float,
        risk_distance: float,
        risk_level: str,
    ) -> RiskResult:


        entry = price


        stop_loss = (

            price

            +

            risk_distance

        )


        take_profit = (

            price

            -

            (

                risk_distance

                *

                self.risk_reward_target

            )

        )


        return RiskResult(

            entry_price=round(
                entry,
                5
            ),


            stop_loss=round(
                stop_loss,
                5
            ),


            take_profit=round(
                take_profit,
                5
            ),


            risk_reward=self.risk_reward_target,


            risk_level=risk_level,


            reason=(

                "Bearish setup risk calculated using ATR and confidence"

            ),

        )



    # ==================================================
    # Main Calculate
    # ==================================================

    def calculate(
        self,
        signal: str,
        current_price: float,
        atr: float | None = None,
        confidence: float = 0.0,
        score: float = 0.0,
        risk_distance: float | None = None,
    ) -> RiskResult:
        """
        Main risk calculation.

        Parameters:

        signal:
            BUY / SELL / NONE

        current_price:
            Current market price

        atr:
            Average True Range value

        confidence:
            Analysis confidence

        score:
            Decision score

        risk_distance:
            Manual override
        """



        distance = (

            self._calculate_risk_distance(

                price=current_price,

                atr=atr,

                risk_distance=risk_distance,

            )

        )



        signal = (

            signal.upper()

        )



        risk_level = (

            self._calculate_risk_level(

                confidence,

                score,

            )

        )



        if signal == "BUY":


            return self._buy_setup(

                price=current_price,

                risk_distance=distance,

                risk_level=risk_level,

            )



        elif signal == "SELL":


            return self._sell_setup(

                price=current_price,

                risk_distance=distance,

                risk_level=risk_level,

            )



        else:


            return RiskResult(

                entry_price=None,

                stop_loss=None,

                take_profit=None,

                risk_reward=None,

                risk_level="NONE",

                reason=(

                    "No trade setup available"

                ),

            )
