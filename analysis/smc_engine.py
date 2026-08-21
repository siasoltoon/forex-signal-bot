from __future__ import annotations

from dataclasses import dataclass



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

    score: float

    strength: float

    reason: str





class SMCEngine:
    """
    Smart Money Concepts Engine.

    Detects:

    - BOS (Break Of Structure)
    - CHoCH (Change Of Character)
    - Liquidity Sweep
    - Order Block
    - Fair Value Gap
    - Market Bias
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

                score=0,

                strength=0,

                reason="Not enough price data.",

            )



        recent = prices[-10:]



        high = max(recent)

        low = min(recent)

        current = recent[-1]



        previous_high = max(
            recent[:-2]
        )


        previous_low = min(
            recent[:-2]
        )



        # =========================
        # Bullish BOS
        # =========================

        if current > previous_high:

            return SMCResult(

                bias="bullish",

                structure="BOS",

                order_block="bullish",

                liquidity="buy_side_taken",

                fair_value_gap=True,

                score=35,

                strength=80,

                reason=(

                    "Bullish Smart Money BOS detected."

                ),

            )



        # =========================
        # Bearish BOS
        # =========================

        if current < previous_low:

            return SMCResult(

                bias="bearish",

                structure="BOS",

                order_block="bearish",

                liquidity="sell_side_taken",

                fair_value_gap=True,

                score=-35,

                strength=80,

                reason=(

                    "Bearish Smart Money BOS detected."

                ),

            )



        # =========================
        # Liquidity Sweep High
        # =========================

        if (

            recent[-2] >= high

            and

            current < recent[-2]

        ):

            return SMCResult(

                bias="bearish",

                structure="CHoCH",

                order_block="bearish",

                liquidity="high_sweep",

                fair_value_gap=False,

                score=-25,

                strength=70,

                reason=(

                    "Liquidity sweep above highs detected."

                ),

            )



        # =========================
        # Liquidity Sweep Low
        # =========================

        if (

            recent[-2] <= low

            and

            current > recent[-2]

        ):

            return SMCResult(

                bias="bullish",

                structure="CHoCH",

                order_block="bullish",

                liquidity="low_sweep",

                fair_value_gap=False,

                score=25,

                strength=70,

                reason=(

                    "Liquidity sweep below lows detected."

                ),

            )



        # =========================
        # Fair Value Gap
        # =========================

        if len(prices) >= 3:

            candle1 = prices[-3]

            candle3 = prices[-1]


            if abs(candle3 - candle1) > abs(current) * 0.002:

                return SMCResult(

                    bias="neutral",

                    structure="range",

                    order_block="none",

                    liquidity="none",

                    fair_value_gap=True,

                    score=10,

                    strength=50,

                    reason=(

                        "Possible Fair Value Gap detected."

                    ),

                )



        return SMCResult(

            bias="neutral",

            structure="none",

            order_block="none",

            liquidity="none",

            fair_value_gap=False,

            score=0,

            strength=0,

            reason=(

                "No Smart Money pattern detected."

            ),

        )
