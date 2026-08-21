from __future__ import annotations


from dataclasses import dataclass



@dataclass(
    frozen=True
)
class ElliottResult:
    """
    Elliott Wave analysis result.
    """

    wave: str

    score: float

    confidence: float

    reason: str



class ElliottEngine:
    """
    Basic Elliott Wave analysis engine.

    Detects:

    - Impulse trend
    - Correction
    - Neutral structure

    Future upgrades:

    - Wave 1-5 detection
    - ABC correction
    - Fibonacci relationships
    - Wave degree analysis
    """



    def analyze(
        self,
        closes: list[float],
    ) -> ElliottResult:


        if len(closes) < 5:

            return ElliottResult(

                wave="unknown",

                score=0,

                confidence=0,

                reason="Not enough price data.",

            )



        # =========================
        # Simple structure detection
        # =========================


        first = closes[0]

        last = closes[-1]



        change = (

            last - first

        )



        percentage = (

            abs(change)

            /

            first

        )



        # =========================
        # Bullish impulse
        # =========================

        if (

            change > 0

            and

            percentage > 0.01

        ):


            return ElliottResult(

                wave="bullish_impulse",

                score=15,

                confidence=70,

                reason=(

                    "Possible bullish Elliott impulse structure."

                ),

            )



        # =========================
        # Bearish impulse
        # =========================

        if (

            change < 0

            and

            percentage > 0.01

        ):


            return ElliottResult(

                wave="bearish_impulse",

                score=-15,

                confidence=70,

                reason=(

                    "Possible bearish Elliott impulse structure."

                ),

            )



        # =========================
        # Correction
        # =========================

        return ElliottResult(

            wave="correction",

            score=0,

            confidence=40,

            reason=(

                "Possible corrective Elliott structure."

            ),

        )
