from __future__ import annotations

from dataclasses import dataclass



@dataclass(
    frozen=True
)
class HarmonicResult:
    """
    Harmonic pattern analysis result.
    """

    pattern: str

    score: float

    strength: float

    reason: str



class HarmonicEngine:
    """
    Detects harmonic trading patterns.

    Supported:

    - AB=CD
    - Gartley
    - Bat
    - Butterfly
    - Crab

    Fibonacci based detection.
    """



    def analyze(
        self,
        prices: list[float],
    ) -> HarmonicResult:



        if len(prices) < 5:

            return HarmonicResult(
                pattern="none",
                score=0,
                strength=0,
                reason="Not enough price data.",
            )



        x = prices[-5]
        a = prices[-4]
        b = prices[-3]
        c = prices[-2]
        d = prices[-1]



        xa = abs(a - x)

        ab = abs(b - a)

        bc = abs(c - b)

        cd = abs(d - c)



        if xa == 0:

            return HarmonicResult(
                pattern="none",
                score=0,
                strength=0,
                reason="Invalid harmonic structure.",
            )



        bullish = d > c



        # =========================
        # AB = CD
        # =========================

        if self._ratio_match(
            ab,
            cd,
            1.0,
            0.15,
        ):

            return HarmonicResult(

                pattern="AB_CD",

                score=(
                    15
                    if bullish
                    else -15
                ),

                strength=75,

                reason=(
                    "AB=CD harmonic pattern detected."
                ),

            )



        # =========================
        # Gartley
        # =========================

        if (

            self._ratio_match(
                ab,
                xa,
                0.618,
            )

            and

            self._ratio_match(
                cd,
                xa,
                0.786,
            )

        ):

            return HarmonicResult(

                pattern="Gartley",

                score=(
                    20
                    if bullish
                    else -20
                ),

                strength=85,

                reason=(
                    "Gartley harmonic pattern detected."
                ),

            )



        # =========================
        # Bat
        # =========================

        if (

            self._ratio_match(
                ab,
                xa,
                0.50,
            )

            and

            self._ratio_match(
                cd,
                xa,
                0.886,
            )

        ):

            return HarmonicResult(

                pattern="Bat",

                score=(
                    18
                    if bullish
                    else -18
                ),

                strength=80,

                reason=(
                    "Bat harmonic pattern detected."
                ),

            )



        # =========================
        # Butterfly
        # =========================

        if self._ratio_match(
            cd,
            xa,
            1.27,
        ):

            return HarmonicResult(

                pattern="Butterfly",

                score=(
                    22
                    if bullish
                    else -22
                ),

                strength=88,

                reason=(
                    "Butterfly harmonic pattern detected."
                ),

            )



        # =========================
        # Crab
        # =========================

        if self._ratio_match(
            cd,
            xa,
            1.618,
        ):

            return HarmonicResult(

                pattern="Crab",

                score=(
                    25
                    if bullish
                    else -25
                ),

                strength=90,

                reason=(
                    "Crab harmonic pattern detected."
                ),

            )



        return HarmonicResult(

            pattern="none",

            score=0,

            strength=0,

            reason=(
                "No harmonic pattern detected."
            ),

        )



    # =========================
    # Fibonacci Ratio Checker
    # =========================

    @staticmethod
    def _ratio_match(
        value: float,
        reference: float,
        target: float,
        tolerance: float = 0.12,
    ) -> bool:



        if reference == 0:

            return False



        ratio = (
            value / reference
        )



        return (

            target - tolerance

            <=

            ratio

            <=

            target + tolerance

        )
