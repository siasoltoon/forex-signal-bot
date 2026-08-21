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
    Professional trade risk output.
    """


    entry_price: float | None


    stop_loss: float | None


    take_profit: float | None


    take_profit_1: float | None


    take_profit_2: float | None


    take_profit_3: float | None


    risk_reward: float | None


    position_size: float | None


    risk_amount: float | None


    trailing_stop: float | None


    risk_level: str


    market_condition: str


    reason: str





# ==================================================
# Risk Engine
# ==================================================

class RiskEngine:
    """
    Professional risk management engine.

    Features:

    - ATR Stop Loss
    - Multi Take Profit
    - Position Sizing
    - Risk Percentage
    - Trailing Stop
    - Market Condition Filter
    - Confidence Based Risk
    """



    def __init__(
        self,
        risk_reward_target: float = 2.0,
        atr_multiplier: float = 1.5,
        account_balance: float = 1000.0,
        risk_percent: float = 1.0,
    ) -> None:


        self.risk_reward_target = (
            risk_reward_target
        )


        self.atr_multiplier = (
            atr_multiplier
        )


        self.account_balance = (
            account_balance
        )


        self.risk_percent = (
            risk_percent
        )



    # ==================================================
    # Risk Level
    # ==================================================

    @staticmethod
    def _calculate_risk_level(
        confidence: float,
        score: float,
    ) -> str:


        if (

            confidence >= 0.80

            and

            abs(score) >= 60

        ):

            return "LOW"



        elif confidence >= 0.50:

            return "MEDIUM"



        return "HIGH"




    # ==================================================
    # Market Condition
    # ==================================================

    @staticmethod
    def _market_condition(
        atr: float | None,
        price: float,
    ) -> str:


        if atr is None:

            return "NORMAL"



        atr_percent = (

            atr

            /

            price

        ) * 100



        if atr_percent < 0.2:

            return "LOW_VOLATILITY"



        elif atr_percent > 2:

            return "HIGH_VOLATILITY"



        return "NORMAL"




    # ==================================================
    # Risk Distance
    # ==================================================

    def _calculate_risk_distance(
        self,
        price: float,
        atr: float | None = None,
        risk_distance: float | None = None,
    ) -> float:


        if risk_distance is not None:

            return abs(
                risk_distance
            )



        if atr and atr > 0:

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
    # Position Size
    # ==================================================

    def _calculate_position_size(
        self,
        risk_distance: float,
    ) -> tuple[float, float]:
        """
        Calculates position size.

        Returns:

        position_size
        risk_amount
        """


        risk_amount = (

            self.account_balance

            *

            (

                self.risk_percent

                /

                100

            )

        )


        if risk_distance <= 0:

            return (

                0.0,

                risk_amount

            )


        position_size = (

            risk_amount

            /

            risk_distance

        )


        return (

            round(

                position_size,

                4

            ),

            round(

                risk_amount,

                2

            ),

        )




    # ==================================================
    # BUY Setup
    # ==================================================

    def _buy_setup(
        self,
        price: float,
        risk_distance: float,
        risk_level: str,
        market_condition: str,
    ) -> RiskResult:


        stop_loss = (

            price

            -

            risk_distance

        )


        tp1 = (

            price

            +

            risk_distance

        )


        tp2 = (

            price

            +

            (

                risk_distance

                *

                2

            )

        )


        tp3 = (

            price

            +

            (

                risk_distance

                *

                3

            )

        )


        position_size, risk_amount = (

            self._calculate_position_size(

                risk_distance

            )

        )


        return RiskResult(

            entry_price=round(
                price,
                5
            ),


            stop_loss=round(
                stop_loss,
                5
            ),


            take_profit=round(
                tp2,
                5
            ),


            take_profit_1=round(
                tp1,
                5
            ),


            take_profit_2=round(
                tp2,
                5
            ),


            take_profit_3=round(
                tp3,
                5
            ),


            risk_reward=2.0,


            position_size=position_size,


            risk_amount=risk_amount,


            trailing_stop=round(
                tp1,
                5
            ),


            risk_level=risk_level,


            market_condition=market_condition,


            reason=(

                "Professional bullish risk plan created"

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
        market_condition: str,
    ) -> RiskResult:


        stop_loss = (

            price

            +

            risk_distance

        )


        tp1 = (

            price

            -

            risk_distance

        )


        tp2 = (

            price

            -

            (

                risk_distance

                *

                2

            )

        )


        tp3 = (

            price

            -

            (

                risk_distance

                *

                3

            )

        )


        position_size, risk_amount = (

            self._calculate_position_size(

                risk_distance

            )

        )


        return RiskResult(

            entry_price=round(
                price,
                5
            ),


            stop_loss=round(
                stop_loss,
                5
            ),


            take_profit=round(
                tp2,
                5
            ),


            take_profit_1=round(
                tp1,
                5
            ),


            take_profit_2=round(
                tp2,
                5
            ),


            take_profit_3=round(
                tp3,
                5
            ),


            risk_reward=2.0,


            position_size=position_size,


            risk_amount=risk_amount,


            trailing_stop=round(
                tp1,
                5
            ),


            risk_level=risk_level,


            market_condition=market_condition,


            reason=(

                "Professional bearish risk plan created"

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



        distance = (

            self._calculate_risk_distance(

                price=current_price,

                atr=atr,

                risk_distance=risk_distance,

            )

        )


        signal = signal.upper()



        risk_level = (

            self._calculate_risk_level(

                confidence,

                score,

            )

        )


        market_condition = (

            self._market_condition(

                atr,

                current_price,

            )

        )



        if signal == "BUY":


            return self._buy_setup(

                price=current_price,

                risk_distance=distance,

                risk_level=risk_level,

                market_condition=market_condition,

            )



        elif signal == "SELL":


            return self._sell_setup(

                price=current_price,

                risk_distance=distance,

                risk_level=risk_level,

                market_condition=market_condition,

            )



        return RiskResult(

            entry_price=None,

            stop_loss=None,

            take_profit=None,

            take_profit_1=None,

            take_profit_2=None,

            take_profit_3=None,

            risk_reward=None,

            position_size=None,

            risk_amount=None,

            trailing_stop=None,

            risk_level="NONE",

            market_condition=market_condition,

            reason=(

                "No trade setup available"

            ),

        )
