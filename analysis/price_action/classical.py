from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class CandlePattern:
    index: Any
    pattern: str
    direction: str
    strength: float


class ClassicalPriceActionAnalyzer:
    """
    Classical price-action analyzer.

    Detects common candle and price-action patterns:
    - Doji
    - Hammer
    - Shooting Star
    - Bullish/Bearish Engulfing
    - Inside Bar
    - Pin Bar
    - Strong bullish/bearish candles
    - Basic support/resistance
    - Breakout conditions
    """

    def __init__(
        self,
        lookback: int = 20,
    ) -> None:
        if lookback < 5:
            raise ValueError(
                "lookback must be >= 5."
            )

        self.lookback = lookback

    @staticmethod
    def _validate(
        dataframe: pd.DataFrame,
    ) -> None:
        required = [
            "open",
            "high",
            "low",
            "close",
        ]

        missing = [
            column
            for column in required
            if column not in dataframe.columns
        ]

        if missing:
            raise ValueError(
                f"Missing columns: {missing}"
            )

        if dataframe.empty:
            raise ValueError(
                "DataFrame cannot be empty."
            )

    @staticmethod
    def _candle_metrics(
        row: pd.Series,
    ) -> dict[str, float]:
        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])

        body = abs(close - open_price)
        candle_range = max(high - low, 1e-12)

        upper_wick = (
            high - max(open_price, close)
        )

        lower_wick = (
            min(open_price, close) - low
        )

        body_ratio = (
            body / candle_range
        )

        upper_ratio = (
            upper_wick / candle_range
        )

        lower_ratio = (
            lower_wick / candle_range
        )

        return {
            "body": body,
            "range": candle_range,
            "upper_wick": upper_wick,
            "lower_wick": lower_wick,
            "body_ratio": body_ratio,
            "upper_ratio": upper_ratio,
            "lower_ratio": lower_ratio,
        }

    def detect_candlestick_patterns(
        self,
        dataframe: pd.DataFrame,
    ) -> list[CandlePattern]:

        self._validate(dataframe)

        patterns: list[CandlePattern] = []

        for i in range(len(dataframe)):

            row = dataframe.iloc[i]

            metrics = self._candle_metrics(row)

            body_ratio = metrics["body_ratio"]
            upper_ratio = metrics["upper_ratio"]
            lower_ratio = metrics["lower_ratio"]

            open_price = float(row["open"])
            close = float(row["close"])

            is_bullish = close > open_price
            is_bearish = close < open_price

            index = dataframe.index[i]

            # --------------------------------------
            # Doji
            # --------------------------------------

            if body_ratio <= 0.10:
                patterns.append(
                    CandlePattern(
                        index=index,
                        pattern="doji",
                        direction="neutral",
                        strength=0.60,
                    )
                )

            # --------------------------------------
            # Hammer
            # --------------------------------------

            if (
                lower_ratio >= 0.55
                and upper_ratio <= 0.20
                and body_ratio <= 0.40
            ):
                patterns.append(
                    CandlePattern(
                        index=index,
                        pattern="hammer",
                        direction="bullish",
                        strength=0.75,
                    )
                )

            # --------------------------------------
            # Shooting Star
            # --------------------------------------

            if (
                upper_ratio >= 0.55
                and lower_ratio <= 0.20
                and body_ratio <= 0.40
            ):
                patterns.append(
                    CandlePattern(
                        index=index,
                        pattern="shooting_star",
                        direction="bearish",
                        strength=0.75,
                    )
                )

            # --------------------------------------
            # Strong candle
            # --------------------------------------

            if body_ratio >= 0.70:

                if is_bullish:
                    patterns.append(
                        CandlePattern(
                            index=index,
                            pattern="strong_bullish_candle",
                            direction="bullish",
                            strength=min(
                                1.0,
                                body_ratio,
                            ),
                        )
                    )

                elif is_bearish:
                    patterns.append(
                        CandlePattern(
                            index=index,
                            pattern="strong_bearish_candle",
                            direction="bearish",
                            strength=min(
                                1.0,
                                body_ratio,
                            ),
                        )
                    )

            # --------------------------------------
            # Pin bar
            # --------------------------------------

            if (
                lower_ratio >= 0.60
                and body_ratio <= 0.35
            ):
                patterns.append(
                    CandlePattern(
                        index=index,
                        pattern="bullish_pin_bar",
                        direction="bullish",
                        strength=0.80,
                    )
                )

            if (
                upper_ratio >= 0.60
                and body_ratio <= 0.35
            ):
                patterns.append(
                    CandlePattern(
                        index=index,
                        pattern="bearish_pin_bar",
                        direction="bearish",
                        strength=0.80,
                    )
                )

        return patterns

    def detect_engulfing(
        self,
        dataframe: pd.DataFrame,
    ) -> list[CandlePattern]:

        self._validate(dataframe)

        patterns: list[CandlePattern] = []

        for i in range(1, len(dataframe)):

            previous = dataframe.iloc[i - 1]
            current = dataframe.iloc[i]

            prev_open = float(previous["open"])
            prev_close = float(previous["close"])

            current_open = float(current["open"])
            current_close = float(current["close"])

            index = dataframe.index[i]

            previous_bullish = (
                prev_close > prev_open
            )

            previous_bearish = (
                prev_close < prev_open
            )

            current_bullish = (
                current_close > current_open
            )

            current_bearish = (
                current_close < current_open
            )

            # Bullish engulfing
            if (
                previous_bearish
                and current_bullish
                and current_open <= prev_close
                and current_close >= prev_open
            ):
                patterns.append(
                    CandlePattern(
                        index=index,
                        pattern="bullish_engulfing",
                        direction="bullish",
                        strength=0.85,
                    )
                )

            # Bearish engulfing
            if (
                previous_bullish
                and current_bearish
                and current_open >= prev_close
                and current_close <= prev_open
            ):
                patterns.append(
                    CandlePattern(
                        index=index,
                        pattern="bearish_engulfing",
                        direction="bearish",
                        strength=0.85,
                    )
                )

        return patterns

    def detect_inside_bars(
        self,
        dataframe: pd.DataFrame,
    ) -> list[CandlePattern]:

        self._validate(dataframe)

        patterns: list[CandlePattern] = []

        for i in range(1, len(dataframe)):

            previous = dataframe.iloc[i - 1]
            current = dataframe.iloc[i]

            inside = (
                float(current["high"])
                <= float(previous["high"])
                and
                float(current["low"])
                >= float(previous["low"])
            )

            if inside:
                patterns.append(
                    CandlePattern(
                        index=dataframe.index[i],
                        pattern="inside_bar",
                        direction="neutral",
                        strength=0.65,
                    )
                )

        return patterns

    def detect_support_resistance(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, float | None]:

        self._validate(dataframe)

        recent = dataframe.tail(
            self.lookback
        )

        support = float(
            recent["low"].min()
        )

        resistance = float(
            recent["high"].max()
        )

        return {
            "support": support,
            "resistance": resistance,
        }

    def detect_breakout(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        self._validate(dataframe)

        if len(dataframe) < (
            self.lookback + 1
        ):
            return {
                "breakout": False,
                "direction": "neutral",
                "level": None,
            }

        previous = dataframe.iloc[
            :-1
        ].tail(self.lookback)

        current = dataframe.iloc[-1]

        previous_high = float(
            previous["high"].max()
        )

        previous_low = float(
            previous["low"].min()
        )

        current_close = float(
            current["close"]
        )

        if current_close > previous_high:
            return {
                "breakout": True,
                "direction": "bullish",
                "level": previous_high,
            }

        if current_close < previous_low:
            return {
                "breakout": True,
                "direction": "bearish",
                "level": previous_low,
            }

        return {
            "breakout": False,
            "direction": "neutral",
            "level": None,
        }

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        patterns = (
            self.detect_candlestick_patterns(
                dataframe
            )
        )

        patterns.extend(
            self.detect_engulfing(
                dataframe
            )
        )

        patterns.extend(
            self.detect_inside_bars(
                dataframe
            )
        )

        support_resistance = (
            self.detect_support_resistance(
                dataframe
            )
        )

        breakout = (
            self.detect_breakout(
                dataframe
            )
        )

        recent_patterns = [
            pattern
            for pattern in patterns
            if pattern.index
            in dataframe.tail(5).index
        ]

        bullish_count = sum(
            1
            for pattern in recent_patterns
            if pattern.direction == "bullish"
        )

        bearish_count = sum(
            1
            for pattern in recent_patterns
            if pattern.direction == "bearish"
        )

        if bullish_count > bearish_count:
            bias = "bullish"

        elif bearish_count > bullish_count:
            bias = "bearish"

        else:
            bias = "neutral"

        return {
            "bias": bias,
            "patterns": recent_patterns,
            "support": support_resistance[
                "support"
            ],
            "resistance": support_resistance[
                "resistance"
            ],
            "breakout": breakout,
        }
