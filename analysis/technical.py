from __future__ import annotations

from typing import Any

import pandas as pd

from analysis.indicators import IndicatorEngine
from analysis.market_structure import (
    MarketStructureAnalyzer,
)


class TechnicalAnalyzer:
    """
    Combines indicators and market structure into
    a normalized technical-analysis report.

    This class does not place trades.
    """

    def __init__(
        self,
        swing_window: int = 2,
    ) -> None:

        self.structure_analyzer = (
            MarketStructureAnalyzer(
                swing_window=swing_window
            )
        )

    @staticmethod
    def _latest_value(
        series: pd.Series,
    ) -> float | None:

        if series.empty:
            return None

        value = series.iloc[-1]

        if pd.isna(value):
            return None

        return float(value)

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        if dataframe.empty:
            raise ValueError(
                "Cannot analyze an empty DataFrame."
            )

        indicators = IndicatorEngine(
            dataframe
        )

        calculated = (
            indicators.calculate_all()
        )

        structure = (
            self.structure_analyzer.analyze(
                dataframe
            )
        )

        latest = calculated.iloc[-1]

        close = float(
            latest["close"]
        )

        rsi = self._latest_value(
            calculated["rsi_14"]
        )

        atr = self._latest_value(
            calculated["atr_14"]
        )

        adx = self._latest_value(
            calculated["adx"]
        )

        macd = self._latest_value(
            calculated["macd"]
        )

        macd_signal = self._latest_value(
            calculated["macd_signal"]
        )

        ema_20 = self._latest_value(
            calculated["ema_20"]
        )

        ema_50 = self._latest_value(
            calculated["ema_50"]
        )

        ema_200 = self._latest_value(
            calculated["ema_200"]
        )

        bullish_factors = 0
        bearish_factors = 0

        # ------------------------------------------
        # RSI
        # ------------------------------------------

        if rsi is not None:

            if rsi > 50:
                bullish_factors += 1

            elif rsi < 50:
                bearish_factors += 1

        # ------------------------------------------
        # MACD
        # ------------------------------------------

        if (
            macd is not None
            and macd_signal is not None
        ):

            if macd > macd_signal:
                bullish_factors += 1

            elif macd < macd_signal:
                bearish_factors += 1

        # ------------------------------------------
        # EMA alignment
        # ------------------------------------------

        if (
            ema_20 is not None
            and ema_50 is not None
        ):

            if ema_20 > ema_50:
                bullish_factors += 1

            elif ema_20 < ema_50:
                bearish_factors += 1

        if (
            ema_50 is not None
            and ema_200 is not None
        ):

            if ema_50 > ema_200:
                bullish_factors += 1

            elif ema_50 < ema_200:
                bearish_factors += 1

        # ------------------------------------------
        # ADX
        # ------------------------------------------

        if adx is not None and adx >= 25:

            if bullish_factors > bearish_factors:
                bullish_factors += 1

            elif bearish_factors > bullish_factors:
                bearish_factors += 1

        # ------------------------------------------
        # Market structure
        # ------------------------------------------

        trend = structure["trend"]

        if trend == "bullish":
            bullish_factors += 2

        elif trend == "bearish":
            bearish_factors += 2

        # ------------------------------------------
        # Determine technical bias
        # ------------------------------------------

        if (
            bullish_factors > bearish_factors
        ):
            bias = "bullish"

        elif (
            bearish_factors > bullish_factors
        ):
            bias = "bearish"

        else:
            bias = "neutral"

        total_factors = (
            bullish_factors
            + bearish_factors
        )

        if total_factors > 0:

            confidence = (
                max(
                    bullish_factors,
                    bearish_factors,
                )
                / total_factors
                * 100
            )

        else:
            confidence = 0.0

        return {
            "price": close,

            "bias": bias,

            "confidence": round(
                confidence,
                2,
            ),

            "bullish_factors": (
                bullish_factors
            ),

            "bearish_factors": (
                bearish_factors
            ),

            "trend": trend,

            "rsi": rsi,

            "macd": macd,

            "macd_signal": macd_signal,

            "atr": atr,

            "adx": adx,

            "ema_20": ema_20,

            "ema_50": ema_50,

            "ema_200": ema_200,

            "structure": structure,

            "data": calculated,
        }
