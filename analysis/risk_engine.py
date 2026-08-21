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
    Calculates trade management levels.

    Provides:

    - Entry
    - Stop Loss
    - Take Profit
    - Risk Reward
    - Risk Level
    """



    def __init__(
        self,
        risk_reward_target: float = 2.0,
    ) -> None:


        self.risk_reward_target = (
            risk_reward_target
        )



    # ==================================================
    # Calculate BUY Setup
    # ==================================================

    def _buy_setup(
        self,
        price: float,
        risk_distance: float,
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


            risk_level="MEDIUM",


            reason=(

                "Bullish setup risk calculated"

            ),

        )



    # ==================================================
    # Calculate SELL Setup
    # ==================================================

    def _sell_setup(
        self,
        price: float,
        risk_distance: float,
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


            risk_level="MEDIUM",


            reason=(

                "Bearish setup risk calculated"

            ),

        )



    # ==================================================
    # Main Calculate
    # ==================================================

    def calculate(
        self,
        signal: str,
        current_price: float,
        risk_distance: float | None = None,
    ) -> RiskResult:
        

        if risk_distance is None:

            # Default fallback
            # Later replaced by ATR

            risk_distance = (

                current_price

                *

                0.01

            )



        signal = signal.upper()



        if signal == "BUY":


            return self._buy_setup(

                current_price,

                risk_distance

            )



        elif signal == "SELL":


            return self._sell_setup(

                current_price,

                risk_distance

            )



        else:


            return RiskResult(

                entry_price=None,

                stop_loss=None,

                take_profit=None,

                risk_reward=None,

                risk_level="NONE",

                reason=(

                    "No trade setup"

                ),

            )
