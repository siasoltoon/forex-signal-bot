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


# ==================================================
# Indicator Snapshot
# ==================================================

@dataclass(
    frozen=True
)
class IndicatorSnapshot:
    """
    Complete indicator calculation snapshot.

    Contains:

    - Raw indicator values
    - Interpreted signals
    - Directional score
    - Confidence
    - Explanation reasons
    """

    values: dict[str, Any]


# ==================================================
# Indicator Engine
# ==================================================

class IndicatorEngine:
    """
    Central technical indicator engine.

    Calculates and interprets:

    - SMA
    - EMA
    - RSI
    - MACD
    - Stochastic RSI
    - Bollinger Bands
    - Standard Deviation

    Also provides:

    - Trend interpretation
    - Momentum interpretation
    - Volatility interpretation
    - Directional scoring
    - Indicator confidence
    - Explanation reasons
    """

    def __init__(
        self,
        sma_period: int = 20,
        ema_period: int = 20,
        rsi_period: int = 14,
        bollinger_period: int = 20,
    ) -> None:

        if sma_period < 1:
            raise ValueError(
                "sma_period must be >= 1."
            )

        if ema_period < 1:
            raise ValueError(
                "ema_period must be >= 1."
            )

        if rsi_period < 1:
            raise ValueError(
                "rsi_period must be >= 1."
            )

        if bollinger_period < 1:
            raise ValueError(
                "bollinger_period must be >= 1."
            )

        self.sma_period = sma_period

        self.ema_period = ema_period

        self.rsi_period = rsi_period

        self.bollinger_period = (
            bollinger_period
        )


    # ==================================================
    # Main Calculation
    # ==================================================

    def calculate(
        self,
        closes: list[float],
    ) -> IndicatorSnapshot:

        if not closes:

            raise ValueError(
                "Closes cannot be empty."
            )

        prices = [
            float(price)
            for price in closes
        ]

        indicators: dict[str, Any] = {}


        # ==================================================
        # Moving Averages
        # ==================================================

        sma_values = sma(
            prices,
            self.sma_period,
        )

        ema_values = ema(
            prices,
            self.ema_period,
        )

        indicators["sma_20"] = sma_values

        indicators["ema_20"] = ema_values

        # Keep configurable aliases as well.
        indicators["sma"] = sma_values

        indicators["ema"] = ema_values


        # ==================================================
        # RSI
        # ==================================================

        rsi_values = rsi(
            prices,
            self.rsi_period,
        )

        indicators["rsi"] = rsi_values


        # ==================================================
        # MACD
        # ==================================================

        macd_values = macd(
            prices
        )

        indicators["macd"] = macd_values


        # ==================================================
        # Stochastic RSI
        # ==================================================

        stochastic_values = (
            stochastic_rsi(
                prices
            )
        )

        indicators["stochastic_rsi"] = (
            stochastic_values
        )


        # ==================================================
        # Bollinger Bands
        # ==================================================

        (
            upper,
            middle,
            lower,
        ) = bollinger_bands(
            prices,
            self.bollinger_period,
        )

        indicators["bollinger"] = {

            "upper": upper,

            "middle": middle,

            "lower": lower,

        }


        # ==================================================
        # Standard Deviation
        # ==================================================

        deviation = standard_deviation(
            prices,
            self.bollinger_period,
        )

        indicators[
            "standard_deviation"
        ] = deviation


        # ==================================================
        # Interpretation
        # ==================================================

        interpretation = (
            self._analyze_signals(
                prices,
                rsi_values,
                macd_values,
                ema_values,
                stochastic_values,
                upper,
                middle,
                lower,
            )
        )

        indicators["signals"] = (
            interpretation["signals"]
        )

        indicators["score"] = (
            interpretation["score"]
        )

        indicators["direction"] = (
            interpretation["direction"]
        )

        indicators["confidence"] = (
            interpretation["confidence"]
        )

        indicators["reasons"] = (
            interpretation["reasons"]
        )


        return IndicatorSnapshot(
            values=indicators
        )



    # ==================================================
    # Helpers
    # ==================================================

    @staticmethod
    def _latest_value(
        values: Any,
    ) -> float | None:
        """
        Returns the latest valid numeric value.
        """

        if values is None:
            return None

        if not isinstance(
            values,
            (list, tuple),
        ):
            try:
                return float(values)
            except (
                TypeError,
                ValueError,
            ):
                return None

        for value in reversed(values):

            if value is None:
                continue

            try:
                return float(value)
            except (
                TypeError,
                ValueError,
            ):
                continue

        return None


    @staticmethod
    def _normalize_score(
        score: float,
    ) -> float:
        """
        Keeps indicator score inside
        the standard 0-100 range.
        """

        return max(
            0.0,
            min(
                100.0,
                float(score),
            ),
        )


    @staticmethod
    def _safe_ratio(
        numerator: float,
        denominator: float,
    ) -> float:
        """
        Safe division helper.
        """

        if denominator == 0:
            return 0.0

        return numerator / denominator


    # ==================================================
    # Signal Analysis
    # ==================================================

    def _analyze_signals(
        self,
        closes: list[float],
        rsi_values: list[float | None],
        macd_values: dict[str, list[float | None]],
        ema_values: list[float | None],
        stochastic_values: Any,
        upper_values: Any,
        middle_values: Any,
        lower_values: Any,
    ) -> dict[str, Any]:
        """
        Converts raw indicators into
        structured trading information.
        """

        signals: dict[str, Any] = {}

        reasons: list[str] = []

        score_components: list[float] = []


        # ==================================================
        # Current Price
        # ==================================================

        if not closes:
            return {
                "signals": {},
                "score": 50.0,
                "direction": "neutral",
                "confidence": 0.0,
                "reasons": [
                    "No price data available."
                ],
            }

        latest_price = float(
            closes[-1]
        )


        # ==================================================
        # RSI
        # ==================================================

        latest_rsi = self._latest_value(
            rsi_values
        )

        signals["rsi"] = {

            "value": latest_rsi,

            "state": "unknown",

        }


        if latest_rsi is None:

            rsi_score = 50.0

            signals["rsi"]["state"] = (
                "unknown"
            )

        elif latest_rsi <= 20:

            rsi_score = 65.0

            signals["rsi"]["state"] = (
                "extremely_oversold"
            )

            reasons.append(
                "RSI is extremely oversold."
            )

        elif latest_rsi < 30:

            rsi_score = 60.0

            signals["rsi"]["state"] = (
                "oversold"
            )

            reasons.append(
                "RSI indicates oversold conditions."
            )

        elif latest_rsi >= 80:

            rsi_score = 35.0

            signals["rsi"]["state"] = (
                "extremely_overbought"
            )

            reasons.append(
                "RSI is extremely overbought."
            )

        elif latest_rsi > 70:

            rsi_score = 40.0

            signals["rsi"]["state"] = (
                "overbought"
            )

            reasons.append(
                "RSI indicates overbought conditions."
            )

        elif latest_rsi >= 55:

            rsi_score = 60.0

            signals["rsi"]["state"] = (
                "bullish"
            )

            reasons.append(
                "RSI shows bullish momentum."
            )

        elif latest_rsi <= 45:

            rsi_score = 40.0

            signals["rsi"]["state"] = (
                "bearish"
            )

            reasons.append(
                "RSI shows bearish momentum."
            )

        else:

            rsi_score = 50.0

            signals["rsi"]["state"] = (
                "neutral"
            )


        score_components.append(
            rsi_score
        )


        # ==================================================
        # EMA Trend
        # ==================================================

        latest_ema = self._latest_value(
            ema_values
        )

        signals["ema"] = {

            "value": latest_ema,

            "state": "unknown",

        }


        if latest_ema is None:

            ema_score = 50.0

            signals["ema"]["state"] = (
                "unknown"
            )

        elif latest_price > latest_ema:

            distance = self._safe_ratio(
                latest_price - latest_ema,
                abs(latest_ema),
            )

            ema_score = min(
                70.0,
                55.0 + (
                    distance * 1000.0
                ),
            )

            signals["ema"]["state"] = (
                "bullish"
            )

            reasons.append(
                "Price is above EMA."
            )

        elif latest_price < latest_ema:

            distance = self._safe_ratio(
                latest_ema - latest_price,
                abs(latest_ema),
            )

            ema_score = max(
                30.0,
                45.0 - (
                    distance * 1000.0
                ),
            )

            signals["ema"]["state"] = (
                "bearish"
            )

            reasons.append(
                "Price is below EMA."
            )

        else:

            ema_score = 50.0

            signals["ema"]["state"] = (
                "neutral"
            )


        score_components.append(
            ema_score
        )


        # ==================================================
        # MACD
        # ==================================================

        macd_line = (
            macd_values.get(
                "macd",
                [],
            )
            if isinstance(
                macd_values,
                dict,
            )
            else []
        )

        signal_line = (
            macd_values.get(
                "signal",
                [],
            )
            if isinstance(
                macd_values,
                dict,
            )
            else []
        )

        histogram = (
            macd_values.get(
                "histogram",
                [],
            )
            if isinstance(
                macd_values,
                dict,
            )
            else []
        )


        latest_macd = self._latest_value(
            macd_line
        )

        latest_signal = self._latest_value(
            signal_line
        )

        latest_histogram = (
            self._latest_value(
                histogram
            )
        )


        signals["macd"] = {

            "macd": latest_macd,

            "signal": latest_signal,

            "histogram": latest_histogram,

            "state": "unknown",

        }


        if (
            latest_macd is None
            or latest_signal is None
        ):

            macd_score = 50.0

            signals["macd"]["state"] = (
                "unknown"
            )

        elif latest_macd > latest_signal:

            macd_score = 60.0

            signals["macd"]["state"] = (
                "bullish"
            )

            reasons.append(
                "MACD is above its signal line."
            )

            if (
                latest_histogram is not None
                and latest_histogram > 0
            ):

                macd_score += 5.0

        elif latest_macd < latest_signal:

            macd_score = 40.0

            signals["macd"]["state"] = (
                "bearish"
            )

            reasons.append(
                "MACD is below its signal line."
            )

            if (
                latest_histogram is not None
                and latest_histogram < 0
            ):

                macd_score -= 5.0

        else:

            macd_score = 50.0

            signals["macd"]["state"] = (
                "neutral"
            )


        macd_score = self._normalize_score(
            macd_score
        )

        score_components.append(
            macd_score
        )


        # ==================================================
        # Stochastic RSI
        # ==================================================

        stochastic_latest = (
            self._extract_stochastic_values(
                stochastic_values
            )
        )

        stoch_k = stochastic_latest[
            "k"
        ]

        stoch_d = stochastic_latest[
            "d"
        ]


        signals["stochastic_rsi"] = {

            "k": stoch_k,

            "d": stoch_d,

            "state": "unknown",

        }


        if stoch_k is None:

            stochastic_score = 50.0

            signals[
                "stochastic_rsi"
            ]["state"] = "unknown"

        elif stoch_k <= 20:

            stochastic_score = 60.0

            signals[
                "stochastic_rsi"
            ]["state"] = "oversold"

            reasons.append(
                "Stochastic RSI is oversold."
            )

        elif stoch_k >= 80:

            stochastic_score = 40.0

            signals[
                "stochastic_rsi"
            ]["state"] = "overbought"

            reasons.append(
                "Stochastic RSI is overbought."
            )

        elif (
            stoch_d is not None
            and stoch_k > stoch_d
        ):

            stochastic_score = 57.0

            signals[
                "stochastic_rsi"
            ]["state"] = "bullish"

        elif (
            stoch_d is not None
            and stoch_k < stoch_d
        ):

            stochastic_score = 43.0

            signals[
                "stochastic_rsi"
            ]["state"] = "bearish"

        else:

            stochastic_score = 50.0

            signals[
                "stochastic_rsi"
            ]["state"] = "neutral"


        score_components.append(
            stochastic_score
        )



        # -------------------------
        # Final indicator summary
        # -------------------------

        bullish = 0
        bearish = 0
        neutral = 0

        # EMA trend
        trend = signals.get(
            "trend",
            "sideways"
        )

        if trend == "bullish":
            bullish += 1

        elif trend == "bearish":
            bearish += 1

        else:
            neutral += 1

        # MACD
        macd_signal = signals.get(
            "macd",
            "neutral"
        )

        if macd_signal == "bullish":
            bullish += 1

        elif macd_signal == "bearish":
            bearish += 1

        else:
            neutral += 1

        # RSI
        momentum = signals.get(
            "momentum",
            "neutral"
        )

        if momentum == "oversold":
            bullish += 1

        elif momentum == "overbought":
            bearish += 1

        else:
            neutral += 1

        # -------------------------
        # Indicator bias
        # -------------------------

        if bullish > bearish:
            bias = "bullish"

        elif bearish > bullish:
            bias = "bearish"

        else:
            bias = "neutral"

        # -------------------------
        # Indicator score
        # -------------------------

        total_votes = (
            bullish
            + bearish
            + neutral
        )

        if total_votes <= 0:
            score = 50.0

        else:
            score = (
                50.0
                +
                (
                    (
                        bullish
                        -
                        bearish
                    )
                    /
                    total_votes
                )
                * 50.0
            )

        score = max(
            0.0,
            min(
                100.0,
                score
            )
        )

        # -------------------------
        # Confidence
        # -------------------------

        if total_votes <= 0:
            confidence = 0.0

        else:
            dominant_votes = max(
                bullish,
                bearish,
                neutral
            )

            confidence = (
                dominant_votes
                /
                total_votes
            )

        # -------------------------
        # Final summary
        # -------------------------

        signals["bias"] = bias

        signals["score"] = round(
            score,
            2
        )

        signals["confidence"] = round(
            confidence,
            3
        )

        signals["bullish_votes"] = (
            bullish
        )

        signals["bearish_votes"] = (
            bearish
        )

        signals["neutral_votes"] = (
            neutral
        )

        return signals
