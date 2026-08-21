
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
    Complete indicator output.
    """

    values: dict[str, Any]


# ==================================================
# Indicator Engine
# ==================================================

class IndicatorEngine:
    """
    Central indicator calculation engine.

    Calculates:

    - SMA
    - EMA
    - RSI
    - MACD
    - Stochastic RSI
    - Bollinger Bands
    - Standard Deviation

    Also provides:

    - Indicator interpretation
    - Direction scoring
    - Confidence estimation
    - Human-readable reasons
    """

    # ==================================================
    # Main Calculation
    # ==================================================

    def calculate(
        self,
        closes: list[float],
    ) -> IndicatorSnapshot:

        indicators: dict[str, Any] = {}

        # --------------------------------------------------
        # Normalize input
        # --------------------------------------------------

        closes = [
            float(value)
            for value in closes
            if value is not None
        ]

        # --------------------------------------------------
        # Empty input
        # --------------------------------------------------

        if not closes:

            indicators["sma_20"] = []
            indicators["ema_20"] = []
            indicators["rsi"] = []
            indicators["macd"] = {
                "macd": [],
                "signal": [],
            }
            indicators["stochastic_rsi"] = []
            indicators["bollinger"] = {
                "upper": [],
                "middle": [],
                "lower": [],
            }
            indicators["standard_deviation"] = []

            indicators["signals"] = {
                "signals": {},
                "score": 50.0,
                "direction": "neutral",
                "confidence": 0.0,
                "reasons": [
                    "No price data available."
                ],
            }

            return IndicatorSnapshot(
                values=indicators
            )

        # ==================================================
        # Moving Averages
        # ==================================================

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

        # ==================================================
        # Momentum
        # ==================================================

        rsi_values = rsi(
            closes,
            14,
        )

        macd_values = macd(
            closes,
        )

        stochastic_values = stochastic_rsi(
            closes,
        )

        indicators["rsi"] = rsi_values
        indicators["macd"] = macd_values
        indicators["stochastic_rsi"] = (
            stochastic_values
        )

        # ==================================================
        # Volatility
        # ==================================================

        upper_values, middle_values, lower_values = (
            bollinger_bands(
                closes,
                20,
            )
        )

        indicators["bollinger"] = {
            "upper": upper_values,
            "middle": middle_values,
            "lower": lower_values,
        }

        indicators["standard_deviation"] = (
            standard_deviation(
                closes,
                20,
            )
        )

        # ==================================================
        # Interpretation Layer
        # ==================================================

        indicators["signals"] = (
            self._analyze_signals(
                closes=closes,
                rsi_values=rsi_values,
                macd_values=macd_values,
                ema_values=ema_20,
                stochastic_values=stochastic_values,
                upper_values=upper_values,
                middle_values=middle_values,
                lower_values=lower_values,
            )
        )

        return IndicatorSnapshot(
            values=indicators
        )

    # ==================================================
    # Generic Latest Value
    # ==================================================

    @staticmethod
    def _latest_value(
        values: Any,
    ) -> float | None:

        if values is None:
            return None

        if isinstance(
            values,
            (int, float),
        ):

            return float(values)

        if not isinstance(
            values,
            (list, tuple),
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

    # ==================================================
    # Safe Ratio
    # ==================================================

    @staticmethod
    def _safe_ratio(
        numerator: float,
        denominator: float,
    ) -> float:

        if denominator == 0:
            return 0.0

        return numerator / denominator

    # ==================================================
    # Normalize Score
    # ==================================================

    @staticmethod
    def _normalize_score(
        score: float,
    ) -> float:

        try:

            score = float(score)

        except (
            TypeError,
            ValueError,
        ):

            return 50.0

        return max(
            0.0,
            min(
                100.0,
                score,
            ),
        )



    # ==================================================
    # Extract Stochastic RSI Values
    # ==================================================

    @staticmethod
    def _extract_stochastic_values(
        stochastic_values: Any,
    ) -> dict[str, float | None]:
        """
        Normalize different Stochastic RSI output formats.

        Supported formats:

        1. list[float | None]
        2. tuple/list containing K and D series
        3. dict containing k / d
        4. dict containing %k / %d
        5. dict containing stochastic_k / stochastic_d
        """

        result: dict[str, float | None] = {
            "k": None,
            "d": None,
        }

        if stochastic_values is None:
            return result

        # --------------------------------------------------
        # Dictionary
        # --------------------------------------------------

        if isinstance(
            stochastic_values,
            dict,
        ):

            k_values = (
                stochastic_values.get("k")
                or stochastic_values.get("%k")
                or stochastic_values.get("stoch_k")
                or stochastic_values.get("stochastic_k")
            )

            d_values = (
                stochastic_values.get("d")
                or stochastic_values.get("%d")
                or stochastic_values.get("stoch_d")
                or stochastic_values.get("stochastic_d")
            )

            if isinstance(
                k_values,
                (list, tuple),
            ):

                k_values = (
                    IndicatorEngine._latest_value(
                        k_values
                    )
                )

            if isinstance(
                d_values,
                (list, tuple),
            ):

                d_values = (
                    IndicatorEngine._latest_value(
                        d_values
                    )
                )

            if k_values is not None:

                try:

                    result["k"] = float(
                        k_values
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    pass

            if d_values is not None:

                try:

                    result["d"] = float(
                        d_values
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    pass

            return result

        # --------------------------------------------------
        # List / Tuple
        # --------------------------------------------------

        if isinstance(
            stochastic_values,
            (list, tuple),
        ):

            if not stochastic_values:
                return result

            # --------------------------------------------------
            # Simple series:
            #
            # [None, None, 40, 55, 70]
            # --------------------------------------------------

            if all(
                value is None
                or isinstance(
                    value,
                    (int, float),
                )
                for value in stochastic_values
            ):

                result["k"] = (
                    IndicatorEngine._latest_value(
                        stochastic_values
                    )
                )

                return result

            # --------------------------------------------------
            # Two-series format:
            #
            # (
            #     [K values],
            #     [D values]
            # )
            # --------------------------------------------------

            if len(stochastic_values) >= 2:

                k_values = stochastic_values[0]
                d_values = stochastic_values[1]

                result["k"] = (
                    IndicatorEngine._latest_value(
                        k_values
                    )
                )

                result["d"] = (
                    IndicatorEngine._latest_value(
                        d_values
                    )
                )

        return result

    # ==================================================
    # Stochastic RSI Score
    # ==================================================

    @staticmethod
    def _stochastic_score(
        stochastic_values: dict[str, float | None],
    ) -> tuple[
        float,
        str,
        list[str],
    ]:

        k = stochastic_values.get("k")
        d = stochastic_values.get("d")

        reasons: list[str] = []

        if k is None:

            return (
                50.0,
                "unknown",
                reasons,
            )

        # --------------------------------------------------
        # Extremely oversold
        # --------------------------------------------------

        if k <= 10:

            score = 65.0

            state = "extremely_oversold"

            reasons.append(
                "Stochastic RSI is extremely oversold."
            )

        # --------------------------------------------------
        # Oversold
        # --------------------------------------------------

        elif k < 20:

            score = 60.0

            state = "oversold"

            reasons.append(
                "Stochastic RSI indicates oversold conditions."
            )

        # --------------------------------------------------
        # Extremely overbought
        # --------------------------------------------------

        elif k >= 90:

            score = 35.0

            state = "extremely_overbought"

            reasons.append(
                "Stochastic RSI is extremely overbought."
            )

        # --------------------------------------------------
        # Overbought
        # --------------------------------------------------

        elif k > 80:

            score = 40.0

            state = "overbought"

            reasons.append(
                "Stochastic RSI indicates overbought conditions."
            )

        # --------------------------------------------------
        # Bullish
        # --------------------------------------------------

        elif k >= 55:

            score = 60.0

            state = "bullish"

            reasons.append(
                "Stochastic RSI shows bullish momentum."
            )

        # --------------------------------------------------
        # Bearish
        # --------------------------------------------------

        elif k <= 45:

            score = 40.0

            state = "bearish"

            reasons.append(
                "Stochastic RSI shows bearish momentum."
            )

        # --------------------------------------------------
        # Neutral
        # --------------------------------------------------

        else:

            score = 50.0

            state = "neutral"

        # --------------------------------------------------
        # K / D confirmation
        # --------------------------------------------------

        if d is not None:

            if k > d:

                score += 3.0

                reasons.append(
                    "Stochastic RSI K is above D."
                )

            elif k < d:

                score -= 3.0

                reasons.append(
                    "Stochastic RSI K is below D."
                )

        return (
            IndicatorEngine._normalize_score(
                score
            ),
            state,
            reasons,
        )

    # ==================================================
    # Bollinger Band Analysis
    # ==================================================

    @staticmethod
    def _bollinger_score(
        price: float,
        upper_values: Any,
        middle_values: Any,
        lower_values: Any,
    ) -> tuple[
        float,
        str,
        list[str],
    ]:

        upper = IndicatorEngine._latest_value(
            upper_values
        )

        middle = IndicatorEngine._latest_value(
            middle_values
        )

        lower = IndicatorEngine._latest_value(
            lower_values
        )

        reasons: list[str] = []

        if (
            upper is None
            or lower is None
            or middle is None
        ):

            return (
                50.0,
                "unknown",
                reasons,
            )

        if upper <= lower:

            return (
                50.0,
                "unknown",
                reasons,
            )

        # --------------------------------------------------
        # Below lower band
        # --------------------------------------------------

        if price < lower:

            return (
                65.0,
                "below_lower_band",
                [
                    "Price is below the lower Bollinger Band."
                ],
            )

        # --------------------------------------------------
        # Above upper band
        # --------------------------------------------------

        if price > upper:

            return (
                35.0,
                "above_upper_band",
                [
                    "Price is above the upper Bollinger Band."
                ],
            )

        # --------------------------------------------------
        # Lower half
        # --------------------------------------------------

        if price < middle:

            reasons.append(
                "Price is below the Bollinger middle band."
            )

            return (
                45.0,
                "below_middle",
                reasons,
            )

        # --------------------------------------------------
        # Upper half
        # --------------------------------------------------

        if price > middle:

            reasons.append(
                "Price is above the Bollinger middle band."
            )

            return (
                55.0,
                "above_middle",
                reasons,
            )

        return (
            50.0,
            "middle",
            reasons,
        )

    # ==================================================
    # Main Signal Analysis
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

            signals["rsi"]["state"] = "bullish"

            reasons.append(
                "RSI shows bullish momentum."
            )

        elif latest_rsi <= 45:

            rsi_score = 40.0

            signals["rsi"]["state"] = "bearish"

            reasons.append(
                "RSI shows bearish momentum."
            )

        else:

            rsi_score = 50.0

            signals["rsi"]["state"] = "neutral"

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
            self._normalize_score(
                ema_score
            )
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

        stochastic_score, stochastic_state, stochastic_reasons = (
            self._stochastic_score(
                stochastic_latest
            )
        )

        signals["stochastic_rsi"] = {
            "k": stochastic_latest.get("k"),
            "d": stochastic_latest.get("d"),
            "state": stochastic_state,
        }

        reasons.extend(
            stochastic_reasons
        )

        score_components.append(
            stochastic_score
        )

        # ==================================================
        # Bollinger Bands
        # ==================================================

        (
            bollinger_score,
            bollinger_state,
            bollinger_reasons,
        ) = self._bollinger_score(
            price=latest_price,
            upper_values=upper_values,
            middle_values=middle_values,
            lower_values=lower_values,
        )

        signals["bollinger"] = {
            "state": bollinger_state,
            "upper": self._latest_value(
                upper_values
            ),
            "middle": self._latest_value(
                middle_values
            ),
            "lower": self._latest_value(
                lower_values
            ),
        }

        reasons.extend(
            bollinger_reasons
        )

        score_components.append(
            bollinger_score
        )

        # ==================================================
        # Standard Deviation
        # ==================================================

        # Standard deviation is primarily a
        # volatility measurement, therefore it
        # does not directly create a bullish
        # or bearish directional score here.

        # ==================================================
        # Final Indicator Score
        # ==================================================

        if not score_components:

            final_score = 50.0

        else:

            final_score = (
                sum(score_components)
                /
                len(score_components)
            )

        final_score = self._normalize_score(
            final_score
        )

        # ==================================================
        # Direction
        # ==================================================

        if final_score >= 60:

            direction = "bullish"

        elif final_score <= 40:

            direction = "bearish"

        else:

            direction = "neutral"

        # ==================================================
        # Confidence
        # ==================================================

        confidence = (
            abs(
                final_score - 50.0
            )
            /
            50.0
        )

        confidence = max(
            0.0,
            min(
                1.0,
                confidence,
            ),
        )

        # ==================================================
        # Signal Summary
        # ==================================================

        signals["summary"] = {
            "score": round(
                final_score,
                2,
            ),
            "direction": direction,
            "confidence": round(
                confidence,
                3,
            ),
        }

        # ==================================================
        # Final Result
        # ==================================================

        return {
            "signals": signals,

            "score": round(
                final_score,
                2,
            ),

            "direction": direction,

            "confidence": round(
                confidence,
                3,
            ),

            "reasons": reasons,
        }


