from __future__ import annotations

from dataclasses import dataclass



# ==================================================
# SMC Result
# ==================================================

@dataclass(
    frozen=True
)
class SMCResult:
    """
    Smart Money Concepts analysis result.
    """

    bias: str

    structure: str

    order_block: str

    liquidity: str

    fair_value_gap: bool

    premium_discount: str

    equal_high: bool

    equal_low: bool

    score: float

    strength: float

    reason: str





# ==================================================
# Smart Money Concepts Engine
# ==================================================

class SMCEngine:
    """
    Advanced Smart Money Concepts Engine.

    Detects:

    - Swing High
    - Swing Low
    - BOS
    - CHoCH
    - Liquidity Sweep
    - Equal High
    - Equal Low
    - Order Block
    - Fair Value Gap
    - Premium / Discount Zone
    """



    def analyze(
        self,
        prices: list[float],
    ) -> SMCResult:


        if len(prices) < 10:

            return SMCResult(

                bias="neutral",

                structure="none",

                order_block="none",

                liquidity="none",

                fair_value_gap=False,

                premium_discount="unknown",

                equal_high=False,

                equal_low=False,

                score=0.0,

                strength=0.0,

                reason="Not enough price data.",

            )



        recent = prices[-20:]



        current = recent[-1]



        high = max(
            recent
        )


        low = min(
            recent
        )



        midpoint = (
            high + low
        ) / 2



        # ==================================================
        # Premium / Discount
        # ==================================================

        if current > midpoint:

            premium_discount = "premium"

        else:

            premium_discount = "discount"




        # ==================================================
        # Swing Detection
        # ==================================================

        swing_highs = []

        swing_lows = []



        for i in range(
            2,
            len(recent) - 2
        ):


            if (
                recent[i]
                >
                recent[i - 1]
                and
                recent[i]
                >
                recent[i + 1]
            ):

                swing_highs.append(
                    recent[i]
                )



            if (
                recent[i]
                <
                recent[i - 1]
                and
                recent[i]
                <
                recent[i + 1]
            ):

                swing_lows.append(
                    recent[i]
                )



        last_swing_high = (

            swing_highs[-1]

            if swing_highs

            else high

        )



        last_swing_low = (

            swing_lows[-1]

            if swing_lows

            else low

        )



        # ==================================================
        # Equal High / Equal Low
        # ==================================================

        equal_high = False

        equal_low = False



        if len(swing_highs) >= 2:


            if abs(

                swing_highs[-1]

                -

                swing_highs[-2]

            ) < (

                abs(current)
                *
                0.001

            ):

                equal_high = True




        if len(swing_lows) >= 2:


            if abs(

                swing_lows[-1]

                -

                swing_lows[-2]

            ) < (

                abs(current)
                *
                0.001

            ):

                equal_low = True


        
        # ==================================================
        # Liquidity Sweep Detection
        # ==================================================

        liquidity = "none"

        structure = "none"

        order_block = "none"

        bias = "neutral"

        score = 0.0

        strength = 0.0

        reason = (
            "No Smart Money pattern detected."
        )



        # ==================================================
        # Bullish BOS
        # ==================================================

        if current > last_swing_high:


            bias = "bullish"

            structure = "BOS"

            order_block = "bullish"

            liquidity = (
                "buy_side_taken"
            )

            score = 35

            strength = 80

            reason = (
                "Bullish BOS detected with "
                "buy-side liquidity taken."
            )



        # ==================================================
        # Bearish BOS
        # ==================================================

        elif current < last_swing_low:


            bias = "bearish"

            structure = "BOS"

            order_block = "bearish"

            liquidity = (
                "sell_side_taken"
            )

            score = -35

            strength = 80

            reason = (
                "Bearish BOS detected with "
                "sell-side liquidity taken."
            )



        # ==================================================
        # Liquidity Sweep High
        # ==================================================

        elif (

            len(recent) >= 3

            and

            recent[-2] >= high

            and

            current < recent[-2]

        ):


            bias = "bearish"

            structure = "CHoCH"

            liquidity = (
                "high_sweep"
            )

            order_block = "bearish"

            score = -25

            strength = 70

            reason = (
                "Liquidity sweep above highs "
                "detected."
            )



        # ==================================================
        # Liquidity Sweep Low
        # ==================================================

        elif (

            len(recent) >= 3

            and

            recent[-2] <= low

            and

            current > recent[-2]

        ):


            bias = "bullish"

            structure = "CHoCH"

            liquidity = (
                "low_sweep"
            )

            order_block = "bullish"

            score = 25

            strength = 70

            reason = (
                "Liquidity sweep below lows "
                "detected."
            )



        # ==================================================
        # Fair Value Gap
        # ==================================================

        fair_value_gap = False



        if len(recent) >= 3:


            candle1 = recent[-3]

            candle3 = recent[-1]



            gap = abs(
                candle3 - candle1
            )



            if gap > abs(current) * 0.002:


                fair_value_gap = True



                if score == 0:


                    score = 10

                    strength = 50



                reason += (
                    " Fair Value Gap detected."
                )



        # ==================================================
        # Equal Liquidity Bonus
        # ==================================================

        if equal_high:


            reason += (
                " Equal highs liquidity present."
            )



        if equal_low:


            reason += (
                " Equal lows liquidity present."
            )



        # ==================================================
        # Final Result
        # ==================================================

        return SMCResult(

            bias=bias,

            structure=structure,

            order_block=order_block,

            liquidity=liquidity,

            fair_value_gap=fair_value_gap,

            premium_discount=premium_discount,

            equal_high=equal_high,

            equal_low=equal_low,

            score=score,

            strength=strength,

            reason=reason,

        )
