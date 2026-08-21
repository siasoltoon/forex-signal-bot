from __future__ import annotations

from dataclasses import dataclass



@dataclass(
    frozen=True
)
class WyckoffResult:
    """
    Wyckoff analysis result.
    """

    phase: str

    pattern: str

    score: float

    strength: float

    reason: str





class WyckoffEngine:
    """
    Wyckoff Market Cycle Analysis Engine.

    Detects:

    - Accumulation
    - Distribution
    - Spring
    - Upthrust
    - SOS (Sign Of Strength)
    - SOW (Sign Of Weakness)
    """



    def analyze(
        self,
        prices: list[float],
    ) -> WyckoffResult:


        if len(prices) < 20:

            return WyckoffResult(

                phase="unknown",

                pattern="none",

                score=0,

                strength=0,

                reason="Not enough price data.",

            )



        recent = prices[-20:]



        highest = max(
            recent
        )


        lowest = min(
            recent
        )


        current = recent[-1]



        range_size = (
            highest - lowest
        )



        if range_size == 0:

            return WyckoffResult(

                phase="neutral",

                pattern="flat",

                score=0,

                strength=0,

                reason="Flat market detected.",

            )



        position = (

            current - lowest

        ) / range_size



        # =========================
        # Spring
        # =========================

        if (

            position < 0.15

            and

            current > recent[-2]

        ):

            return WyckoffResult(

                phase="accumulation",

                pattern="spring",

                score=25,

                strength=80,

                reason=(

                    "Wyckoff Spring detected. "

                    "Possible accumulation reversal."

                ),

            )



        # =========================
        # Upthrust
        # =========================

        if (

            position > 0.85

            and

            current < recent[-2]

        ):

            return WyckoffResult(

                phase="distribution",

                pattern="upthrust",

                score=-25,

                strength=80,

                reason=(

                    "Wyckoff Upthrust detected. "

                    "Possible distribution reversal."

                ),

            )



        # =========================
        # Sign Of Strength
        # =========================

        if (

            position > 0.75

            and

            current > recent[-5]

        ):

            return WyckoffResult(

                phase="accumulation",

                pattern="SOS",

                score=20,

                strength=70,

                reason=(

                    "Sign Of Strength detected."

                ),

            )



        # =========================
        # Sign Of Weakness
        # =========================

        if (

            position < 0.25

            and

            current < recent[-5]

        ):

            return WyckoffResult(

                phase="distribution",

                pattern="SOW",

                score=-20,

                strength=70,

                reason=(

                    "Sign Of Weakness detected."

                ),

            )



        # =========================
        # Trading Range
        # =========================

        volatility = (

            range_size

            /

            abs(recent[0])

        )



        if volatility < 0.03:


            return WyckoffResult(

                phase="range",

                pattern="accumulation_distribution",

                score=0,

                strength=50,

                reason=(

                    "Wyckoff trading range detected."

                ),

            )



        return WyckoffResult(

            phase="neutral",

            pattern="none",

            score=0,

            strength=0,

            reason=(

                "No Wyckoff pattern detected."

            ),

        )
