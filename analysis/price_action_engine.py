from __future__ import annotations

from dataclasses import dataclass


@dataclass(
    frozen=True
)
class PriceActionResult:
    """
    Price action analysis result.
    """

    state: str

    score: float

    reasons: list[str]



class PriceActionEngine:
    """
    Price Action analysis engine.

    Detects:
    - Higher Highs
    - Higher Lows
    - Lower Highs
    - Lower Lows
    - Breakouts
    - Momentum candles
    """



    def analyze(
        self,
        closes: list[float],
    ) -> PriceActionResult:


        score = 0

        reasons: list[str] = []


        if len(closes) < 5:

            return PriceActionResult(
                state="neutral",
                score=0,
                reasons=[
                    "Not enough price data."
                ],
            )



        # =====================
        # Market swings
        # =====================

        previous = closes[:-1]

        current = closes[-1]



        highs = self._higher_highs(
            previous,
            current,
        )


        lows = self._higher_lows(
            previous,
            current,
        )



        if highs:

            score += 20

            reasons.append(
                "Higher High structure detected."
            )


        if lows:

            score += 15

            reasons.append(
                "Higher Low structure detected."
            )



        lower_high = (
            self._lower_highs(
                previous,
                current,
            )
        )


        lower_low = (
            self._lower_lows(
                previous,
                current,
            )
        )



        if lower_high:

            score -= 20

            reasons.append(
                "Lower High structure detected."
            )


        if lower_low:

            score -= 15

            reasons.append(
                "Lower Low structure detected."
            )



        # =====================
        # Final state
        # =====================


        if score > 0:

            state = "bullish"


        elif score < 0:

            state = "bearish"


        else:

            state = "neutral"



        return PriceActionResult(
            state=state,
            score=score,
            reasons=reasons,
        )



    @staticmethod
    def _higher_highs(
        values: list[float],
        current: float,
    ) -> bool:

        return current > max(values)



    @staticmethod
    def _higher_lows(
        values: list[float],
        current: float,
    ) -> bool:

        if len(values) < 3:
            return False

        return (
            current > values[-2]
            and
            values[-2] > values[-3]
        )



    @staticmethod
    def _lower_highs(
        values: list[float],
        current: float,
    ) -> bool:

        return current < min(values)



    @staticmethod
    def _lower_lows(
        values: list[float],
        current: float,
    ) -> bool:

        if len(values) < 3:
            return False

        return (
            current < values[-2]
            and
            values[-2] < values[-3]
        )
