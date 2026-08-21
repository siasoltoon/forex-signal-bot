from __future__ import annotations

from dataclasses import dataclass



# ==================================================
# Trade Risk Result
# ==================================================

@dataclass(
    frozen=True
)
class RiskResult:
    """
    Complete risk calculation result.
    """

    entry: float

    stop_loss: float

    take_profit_1: float

    take_profit_2: float

    risk_reward: float

    risk_percent: float

    position_size: float



# ==================================================
# Risk Manager
# ==================================================

class RiskManager:
    """
    Professional risk management engine.

    Features:

    - Stop Loss calculation
    - Take Profit calculation
    - Risk / Reward
    - Position sizing
    """



    def __init__(
        self,
        risk_percent: float = 1.0,
    ) -> None:

        self.risk_percent = risk_percent



    # ==================================================
    # Main Calculation
    # ==================================================

    def calculate(
        self,
        entry: float,
        direction: str,
        account_balance: float = 10000,
        stop_distance: float = 0.0020,
    ) -> RiskResult:


        direction = direction.upper()



        # -------------------------
        # Stop Loss
        # -------------------------

        if direction == "BUY":

            stop_loss = (
                entry
                -
                stop_distance
            )


        else:

            stop_loss = (
                entry
                +
                stop_distance
            )



        # -------------------------
        # Risk Amount
        # -------------------------

        risk_amount = (
            account_balance
            *
            (
                self.risk_percent
                /
                100
            )
        )



        # -------------------------
        # Take Profit
        # -------------------------

        if direction == "BUY":

            take_profit_1 = (
                entry
                +
                (
                    stop_distance
                    *
                    2
                )
            )


            take_profit_2 = (
                entry
                +
                (
                    stop_distance
                    *
                    3
                )
            )


        else:

            take_profit_1 = (
                entry
                -
                (
                    stop_distance
                    *
                    2
                )
            )


            take_profit_2 = (
                entry
                -
                (
                    stop_distance
                    *
                    3
                )
            )

      

        # -------------------------
        # Risk / Reward
        # -------------------------

        reward = abs(
            take_profit_1
            -
            entry
        )


        risk = abs(
            entry
            -
            stop_loss
        )


        if risk == 0:

            risk_reward = 0.0

        else:

            risk_reward = (
                reward
                /
                risk
            )



        # -------------------------
        # Position Size
        # -------------------------

        if risk == 0:

            position_size = 0.0

        else:

            position_size = (
                risk_amount
                /
                risk
            )



        return RiskResult(

            entry=round(
                entry,
                5
            ),


            stop_loss=round(
                stop_loss,
                5
            ),


            take_profit_1=round(
                take_profit_1,
                5
            ),


            take_profit_2=round(
                take_profit_2,
                5
            ),


            risk_reward=round(
                risk_reward,
                2
            ),


            risk_percent=self.risk_percent,


            position_size=round(
                position_size,
                2
            ),

        )
