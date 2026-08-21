from __future__ import annotations

from dataclasses import dataclass



@dataclass(
    frozen=True
)
class BrooksResult:
    """
    Al Brooks price action analysis result.
    """

    pattern: str

    score: float

    strength: float

    reason: str




class BrooksEngine:
    """
    Al Brooks style price action engine.

    Detects:

    - Trend Bars
    - Trading Range
    - Breakout
    - Failed Breakout
    - Pullback
    - Two Legged Pullback

    Returns:
    - Pattern
    - Score
    - Strength
    - Explanation
    """



    def analyze(
        self,
        prices: list[float],
    ) -> BrooksResult:


        if len(prices) < 10:

            return BrooksResult(

                pattern="none",

                score=0,

                strength=0,

                reason="Not enough price data.",

            )



        recent = prices[-10:]



        # =========================
        # Market Direction
        # =========================


        first = recent[0]

        last = recent[-1]


        change = (
            last - first
        )



        average_move = (
            sum(
                abs(
                    recent[i]
                    -
                    recent[i - 1]
                )

                for i in range(
                    1,
                    len(recent)
                )

            )
            /
            9
        )



        # =========================
        # Strong Trend Bar
        # =========================


        if average_move > 0:


            if change > average_move * 3:

                return BrooksResult(

                    pattern="bull_trend_bar",

                    score=20,

                    strength=75,

                    reason=(
                        "Strong bullish trend bar detected."
                    ),

                )



            if change < -average_move * 3:

                return BrooksResult(

                    pattern="bear_trend_bar",

                    score=-20,

                    strength=75,

                    reason=(
                        "Strong bearish trend bar detected."
                    ),

                )



        # =========================
        # Trading Range
        # =========================


        highest = max(
            recent
        )

        lowest = min(
            recent
        )


        range_size = (
            highest - lowest
        )



        if range_size > 0:


            volatility = (
                range_size
                /
                abs(first)
            )



            if volatility < 0.02:


                return BrooksResult(

                    pattern="trading_range",

                    score=0,

                    strength=60,

                    reason=(
                        "Trading range detected."
                    ),

                )



        # =========================
        # Breakout
        # =========================


        previous_high = max(
            recent[:-2]
        )


        previous_low = min(
            recent[:-2]
        )



        if last > previous_high:


            return BrooksResult(

                pattern="bull_breakout",

                score=25,

                strength=80,

                reason=(
                    "Bullish breakout detected."
                ),

            )



        if last < previous_low:


            return BrooksResult(

                pattern="bear_breakout",

                score=-25,

                strength=80,

                reason=(
                    "Bearish breakout detected."
                ),

            )



        # =========================
        # Pullback
        # =========================


        if (
            prices[-1] < prices[-2]
            and
            prices[-2] > prices[-3]
        ):


            return BrooksResult(

                pattern="bull_pullback",

                score=10,

                strength=55,

                reason=(
                    "Bullish pullback structure detected."
                ),

            )



        if (
            prices[-1] > prices[-2]
            and
            prices[-2] < prices[-3]
        ):


            return BrooksResult(

                pattern="bear_pullback",

                score=-10,

                strength=55,

                reason=(
                    "Bearish pullback structure detected."
                ),

            )



        return BrooksResult(

            pattern="none",

            score=0,

            strength=0,

            reason=(
                "No Brooks price action pattern detected."
            ),

        )
