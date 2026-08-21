
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(
    frozen=True
)
class MomentumResult:
    """
    Momentum analysis result.
    """

    state: str

    score: float

    reasons: list[str]



class MomentumEngine:
    """
    Converts indicators into momentum analysis.
    """

    def analyze(
        self,
        indicators: dict[str, Any],
    ) -> MomentumResult:


        score = 0

        reasons: list[str] = []


        # RSI Analysis

        rsi_values = indicators.get(
            "rsi",
            [],
        )


        rsi = self._last_value(
            rsi_values
        )


        if rsi is not None:

            if rsi < 30:
                score += 20

                reasons.append(
                    "RSI is oversold."
                )


            elif rsi > 70:
                score -= 20

                reasons.append(
                    "RSI is overbought."
                )


            else:
                reasons.append(
                    "RSI is neutral."
                )


        # MACD Analysis

        macd_data = indicators.get(
            "macd",
            {}
        )


        macd_value = self._last_value(
            macd_data.get(
                "macd",
                []
            )
        )


        signal_value = self._last_value(
            macd_data.get(
                "signal",
                []
            )
        )


        if (
            macd_value is not None
            and
            signal_value is not None
        ):

            if macd_value > signal_value:

                score += 10

                reasons.append(
                    "MACD is bullish."
                )


            elif macd_value < signal_value:

                score -= 10

                reasons.append(
                    "MACD is bearish."
                )


        # Final state

        if score > 0:

            state = "bullish"


        elif score < 0:

            state = "bearish"


        else:

            state = "neutral"


        return MomentumResult(
            state=state,
            score=score,
            reasons=reasons,
        )



    @staticmethod
    def _last_value(
        values,
    ):

        if not values:
            return None


        for value in reversed(values):

            if value is not None:
                return value


        return None
