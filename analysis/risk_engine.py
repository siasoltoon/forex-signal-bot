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


    lot_size: float | None


    risk_amount: float | None


    risk_percent: float | None


    trailing_stop: float | None


    trade_quality: float | None


    trade_grade: str


    risk_level: str


    market_condition: str


    reason: str





# ==================================================
# Risk Engine
# ==================================================

class RiskEngine:
    """
    Advanced professional risk management engine.

    Features:

    - ATR based stop loss
    - Dynamic risk percentage
    - Position sizing
    - Lot calculation
    - Multi take profit
    - Dynamic risk reward
    - Trailing stop
    - Market volatility filter
    - Trade quality scoring
    """



    def __init__(
        self,
        risk_reward_target: float = 2.0,
        atr_multiplier: float = 1.5,
        account_balance: float = 1000.0,
        risk_percent: float = 1.0,
        contract_size: float = 100000,
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


        self.contract_size = (

            contract_size

        )



    # ==================================================
    # Dynamic Risk Percentage
    # ==================================================

    def _dynamic_risk_percent(
        self,
        confidence: float,
        score: float,
    ) -> float:
        """
        Adjusts risk according to setup quality.
        """


        if (

            confidence >= 0.85

            and

            abs(score) >= 80

        ):

            return 2.0



        elif (

            confidence >= 0.70

            and

            abs(score) >= 60

        ):

            return 1.5



        elif confidence >= 0.50:

            return 1.0



        return 0.5




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


        if atr is None or price <= 0:

            return "UNKNOWN"



        atr_percent = (

            atr

            /

            price

        ) * 100



        if atr_percent < 0.2:

            return "LOW_VOLATILITY"



        elif atr_percent > 3:

            return "EXTREME_VOLATILITY"



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
    # Position Size
    # ==================================================

    def _calculate_position_size(
        self,
        risk_distance: float,
        dynamic_risk_percent: float,
    ) -> tuple[float, float, float]:
        """
        Calculates:

        - Position size
        - Lot size
        - Risk amount
        """


        risk_amount = (

            self.account_balance

            *

            (

                dynamic_risk_percent

                /

                100

            )

        )



        if risk_distance <= 0:

            return (

                0.0,

                0.0,

                risk_amount

            )



        position_size = (

            risk_amount

            /

            risk_distance

        )



        lot_size = (

            position_size

            /

            self.contract_size

        )



        return (

            round(position_size, 4),

            round(lot_size, 3),

            round(risk_amount, 2),

        )




    # ==================================================
    # Trade Quality
    # ==================================================

    @staticmethod
    def _trade_quality(
        confidence: float,
        score: float,
        market_condition: str,
    ) -> tuple[float, str]:
        """
        Calculates setup quality.
        """


        quality = 0.0



        quality += (

            confidence

            *

            50

        )



        quality += (

            min(

                abs(score),

                50

            )

        )



        if market_condition == "NORMAL":

            quality += 10



        elif market_condition == "HIGH_VOLATILITY":

            quality -= 10



        elif market_condition == "EXTREME_VOLATILITY":

            quality -= 20



        quality = max(

            0,

            min(

                quality,

                100

            )

        )



        if quality >= 90:

            grade = "A+"



        elif quality >= 75:

            grade = "A"



        elif quality >= 60:

            grade = "B"



        else:

            grade = "NO_TRADE"



        return (

            round(

                quality,

                2

            ),

            grade

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
        confidence: float,
        score: float,
        risk_percent: float,
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



        position_size, lot_size, risk_amount = (

            self._calculate_position_size(

                risk_distance,

                risk_percent,

            )

        )



        trade_quality, trade_grade = (

            self._trade_quality(

                confidence,

                score,

                market_condition,

            )

        )



        return RiskResult(

            entry_price=round(price, 5),

            stop_loss=round(stop_loss, 5),

            take_profit=round(tp2, 5),

            take_profit_1=round(tp1, 5),

            take_profit_2=round(tp2, 5),

            take_profit_3=round(tp3, 5),

            risk_reward=2.0,

            position_size=position_size,

            lot_size=lot_size,

            risk_amount=risk_amount,

            risk_percent=risk_percent,

            trailing_stop=round(tp1, 5),

            trade_quality=trade_quality,

            trade_grade=trade_grade,

            risk_level=risk_level,

            market_condition=market_condition,

            reason=(

                "Professional bullish risk plan generated"

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
        confidence: float,
        score: float,
        risk_percent: float,
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


        position_size, lot_size, risk_amount = (

            self._calculate_position_size(

                risk_distance,

                risk_percent,

            )

        )


        trade_quality, trade_grade = (

            self._trade_quality(

                confidence,

                score,

                market_condition,

            )

        )


        return RiskResult(

            entry_price=round(price, 5),

            stop_loss=round(stop_loss, 5),

            take_profit=round(tp2, 5),

            take_profit_1=round(tp1, 5),

            take_profit_2=round(tp2, 5),

            take_profit_3=round(tp3, 5),

            risk_reward=2.0,

            position_size=position_size,

            lot_size=lot_size,

            risk_amount=risk_amount,

            risk_percent=risk_percent,

            trailing_stop=round(tp1, 5),

            trade_quality=trade_quality,

            trade_grade=trade_grade,

            risk_level=risk_level,

            market_condition=market_condition,

            reason=(

                "Professional bearish risk plan generated"

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
        Main professional risk calculation.

        Inputs:

        signal:
            BUY / SELL / NONE

        current_price:
            Current market price

        atr:
            Average True Range

        confidence:
            Analysis confidence

        score:
            Decision engine score

        risk_distance:
            Manual stop distance override
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



        market_condition = (

            self._market_condition(

                atr,

                current_price,

            )

        )



        dynamic_risk_percent = (

            self._dynamic_risk_percent(

                confidence,

                score,

            )

        )



        if signal == "BUY":


            return self._buy_setup(

                price=current_price,

                risk_distance=distance,

                risk_level=risk_level,

                market_condition=market_condition,

                confidence=confidence,

                score=score,

                risk_percent=dynamic_risk_percent,

            )



        elif signal == "SELL":


            return self._sell_setup(

                price=current_price,

                risk_distance=distance,

                risk_level=risk_level,

                market_condition=market_condition,

                confidence=confidence,

                score=score,

                risk_percent=dynamic_risk_percent,

            )



        # ==================================================
        # No Trade
        # ==================================================

        trade_quality, trade_grade = (

            self._trade_quality(

                confidence,

                score,

                market_condition,

            )

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

            lot_size=None,

            risk_amount=None,

            risk_percent=dynamic_risk_percent,

            trailing_stop=None,

            trade_quality=trade_quality,

            trade_grade=trade_grade,

            risk_level="NONE",

            market_condition=market_condition,

            reason=(

                "No valid trade setup available"

            ),

        )
