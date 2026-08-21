
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from analysis.indicators import (
    sma,
    ema,
    rsi,
    macd,
    stochastic_rsi,
    bollinger_bands,
    standard_deviation,
)


@dataclass(
    frozen=True
)
class IndicatorSnapshot:
    """
    Complete indicator output.
    """

    values: dict[str, Any]



class IndicatorEngine:
    """
    Central indicator calculation engine.

    Calculates:
    - Moving averages
    - Momentum indicators
    - Volatility indicators
    """

    def calculate(
        self,
        closes: list[float],
    ) -> IndicatorSnapshot:


        indicators: dict[str, Any] = {}


        # Moving averages

        indicators["sma_20"] = sma(
            closes,
            20,
        )

        indicators["ema_20"] = ema(
            closes,
            20,
        )


        # Momentum

        indicators["rsi"] = rsi(
            closes,
            14,
        )


        indicators["macd"] = macd(
            closes
        )


        indicators["stochastic_rsi"] = (
            stochastic_rsi(
                closes
            )
        )


        # Volatility

        upper, middle, lower = (
            bollinger_bands(
                closes,
                20,
            )
        )


        indicators["bollinger"] = {
            "upper": upper,
            "middle": middle,
            "lower": lower,
        }


        indicators["standard_deviation"] = (
            standard_deviation(
                closes,
                20,
            )
        )


        return IndicatorSnapshot(
            values=indicators
        )
