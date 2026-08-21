from __future__ import annotations

from dataclasses import dataclass



@dataclass(
    frozen=True
)
class CandlestickResult:
    """
    Candlestick pattern analysis result.
    """

    pattern: str

    score: float

    strength: float

    reason: str



class CandlestickEngine:
    """
    Detects important candlestick patterns.

    Patterns:
    - Bullish Engulfing
    - Bearish Engulfing
    - Hammer
    - Shooting Star
    - Doji
    """



    def analyze(
        self,
        candles: list[dict[str, float]],
    ) -> CandlestickResult:


        if len(candles) < 2:

            return CandlestickResult(
                pattern="none",
                score=0,
                strength=0,
                reason="Not enough candle data.",
            )



        previous = candles[-2]

        current = candles[-1]



        previous_open = previous["open"]
        previous_close = previous["close"]


        current_open = current["open"]
        current_close = current["close"]


        current_high = current["high"]
        current_low = current["low"]



        body = abs(
            current_close - current_open
        )


        candle_range = (
            current_high - current_low
        )



        if candle_range == 0:

            return CandlestickResult(
                pattern="none",
                score=0,
                strength=0,
                reason="Invalid candle.",
            )



        # =========================
        # Bullish Engulfing
        # =========================

        if (

            previous_close < previous_open

            and

            current_close > current_open

            and

            current_open <= previous_close

            and

            current_close >= previous_open

        ):

            return CandlestickResult(
                pattern="bullish_engulfing",

                score=15,

                strength=90,

                reason=(
                    "Bullish engulfing pattern detected."
                ),
            )



        # =========================
        # Bearish Engulfing
        # =========================

        if (

            previous_close > previous_open

            and

            current_close < current_open

            and

            current_open >= previous_close

            and

            current_close <= previous_open

        ):

            return CandlestickResult(
                pattern="bearish_engulfing",

                score=-15,

                strength=90,

                reason=(
                    "Bearish engulfing pattern detected."
                ),
            )



        # =========================
        # Hammer
        # =========================

        lower_shadow = (
            min(
                current_open,
                current_close,
            )
            -
            current_low
        )


        if (

            lower_shadow > body * 2

            and

            body < candle_range * 0.4

        ):

            return CandlestickResult(
                pattern="hammer",

                score=10,

                strength=70,

                reason=(
                    "Hammer reversal pattern detected."
                ),
            )



        # =========================
        # Shooting Star
        # =========================

        upper_shadow = (
            current_high
            -
            max(
                current_open,
                current_close,
            )
        )


        if (

            upper_shadow > body * 2

            and

            body < candle_range * 0.4

        ):

            return CandlestickResult(
                pattern="shooting_star",

                score=-10,

                strength=70,

                reason=(
                    "Shooting star reversal pattern detected."
                ),
            )



        # =========================
        # Doji
        # =========================

        if body <= candle_range * 0.1:

            return CandlestickResult(
                pattern="doji",

                score=0,

                strength=50,

                reason=(
                    "Doji candle shows market indecision."
                ),
            )



        return CandlestickResult(
            pattern="none",

            score=0,

            strength=0,

            reason=(
                "No candlestick pattern detected."
            ),
        )
