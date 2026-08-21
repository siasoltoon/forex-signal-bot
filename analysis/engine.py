from __future__ import annotations

from dataclasses import dataclass

from analysis.indicators import (
    sma,
    ema,
    rsi,
    macd,
    stochastic_rsi,
)


@dataclass(
    frozen=True
)
class AnalysisResult:
    """
    Standard technical analysis output.
    """

    trend: str

    momentum: str

    indicators: dict[str, object]


class AnalysisEngine:
    """
    Technical analysis engine.

    Responsible for:
    - Running indicators.
    - Detecting trend.
    - Detecting momentum.
    - Producing normalized analysis result.
    """

    def analyze(
        self,
        closes: list[float],
    ) -> AnalysisResult:
        """
        Analyze close prices.
        """

        if not isinstance(
            closes,
            list,
        ):
            raise TypeError(
                "closes must be a list."
            )

        if len(closes) == 0:
            raise ValueError(
                "closes cannot be empty."
            )

        moving_average = {
            "sma": sma(
                closes,
                period=20,
            ),
            "ema": ema(
                closes,
                period=20,
            ),
        }

        momentum = {
            "rsi": rsi(
                closes,
                period=14,
            ),
            "macd": macd(
                closes,
            ),
            "stochastic_rsi": stochastic_rsi(
                closes,
            ),
        }

        trend = self._detect_trend(
            closes,
            moving_average,
        )

        momentum_state = self._detect_momentum(
            momentum,
        )

        return AnalysisResult(
            trend=trend,
            momentum=momentum_state,
            indicators={
                **moving_average,
                **momentum,
            },
        )


    @staticmethod
    def _detect_trend(
        closes: list[float],
        averages: dict[str, object],
    ) -> str:
        """
        Basic trend detection.
        """

        sma_values = averages["sma"]

        if not sma_values:
            return "unknown"

        last_sma = sma_values[-1]

        if last_sma is None:
            return "unknown"

        last_price = closes[-1]

        if last_price > last_sma:
            return "bullish"

        if last_price < last_sma:
            return "bearish"

        return "sideways"


    @staticmethod
    def _detect_momentum(
        indicators: dict[str, object],
    ) -> str:
        """
        Basic momentum detection.
        """

        rsi_values = indicators["rsi"]

        if not rsi_values:
            return "unknown"

        last_rsi = rsi_values[-1]

        if last_rsi is None:
            return "unknown"

        if last_rsi >= 70:
            return "overbought"

        if last_rsi <= 30:
            return "oversold"

        return "neutral"
