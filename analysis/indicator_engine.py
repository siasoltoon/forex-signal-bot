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
    - Basic indicator interpretation
    """



    def calculate(
        self,
        closes: list[float],
    ) -> IndicatorSnapshot:


        indicators: dict[str, Any] = {}



        # =========================
        # Moving averages
        # =========================

        sma_20 = sma(
            closes,
            20,
        )

        ema_20 = ema(
            closes,
            20,
        )


        indicators["sma_20"] = sma_20

        indicators["ema_20"] = ema_20



        # =========================
        # Momentum
        # =========================

        rsi_values = rsi(
            closes,
            14,
        )

        macd_values = macd(
            closes
        )

        stochastic_values = stochastic_rsi(
            closes
        )


        indicators["rsi"] = rsi_values

        indicators["macd"] = macd_values

        indicators["stochastic_rsi"] = (
            stochastic_values
        )



        # =========================
        # Volatility
        # =========================

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



        # =========================
        # Interpretation Layer
        # =========================


        indicators["signals"] = (
            self._analyze_signals(
                closes,
                rsi_values,
                macd_values,
                ema_20,
            )
        )



        return IndicatorSnapshot(
            values=indicators
        )





    @staticmethod
    def _analyze_signals(
        closes: list[float],
        rsi_values: list[float | None],
        macd_values: dict[str, list[float | None]],
        ema_values: list[float | None],
    ) -> dict[str, Any]:
        """
        Convert raw indicators into trading information.
        """


        signals: dict[str, Any] = {}



        # -------------------------
        # RSI
        # -------------------------

        latest_rsi = next(
            (
                value
                for value in reversed(rsi_values)
                if value is not None
            ),
            None,
        )


        if latest_rsi is None:

            signals["momentum"] = "neutral"


        elif latest_rsi < 30:

            signals["momentum"] = "oversold"


        elif latest_rsi > 70:

            signals["momentum"] = "overbought"


        else:

            signals["momentum"] = "neutral"




        # -------------------------
        # EMA trend
        # -------------------------

        latest_price = closes[-1]

        latest_ema = next(
            (
                value
                for value in reversed(ema_values)
                if value is not None
            ),
            None,
        )


        if latest_ema is None:

            signals["trend"] = "sideways"


        elif latest_price > latest_ema:

            signals["trend"] = "bullish"


        elif latest_price < latest_ema:

            signals["trend"] = "bearish"


        else:

            signals["trend"] = "sideways"




        # -------------------------
        # MACD
        # -------------------------

        macd_line = macd_values.get(
            "macd",
            []
        )

        signal_line = macd_values.get(
            "signal",
            []
        )


        latest_macd = next(
            (
                value
                for value in reversed(macd_line)
                if value is not None
            ),
            None,
        )


        latest_signal = next(
            (
                value
                for value in reversed(signal_line)
                if value is not None
            ),
            None,
        )


        if (
            latest_macd is None
            or
            latest_signal is None
        ):

            signals["macd"] = "neutral"


        elif latest_macd > latest_signal:

            signals["macd"] = "bullish"


        elif latest_macd < latest_signal:

            signals["macd"] = "bearish"


        else:

            signals["macd"] = "neutral"



        return signals
