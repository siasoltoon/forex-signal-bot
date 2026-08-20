from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class BarSignal:
    index: Any
    bar_type: str
    direction: str
    strength: float


@dataclass(frozen=True)
class PriceActionPattern:
    index: Any
    pattern: str
    direction: str
    score: float
    details: dict[str, Any]


class AlBrooksAnalyzer:
    """
    Initial Al Brooks style price-action engine.

    Detects contextual price-action concepts such as:
    - Trend bars
    - Signal bars
    - Breakouts
    - Failed breakouts
    - Pullbacks
    - Two-legged pullbacks
    - Trading ranges
    - Basic High/Low 1-2-3 structures

    This engine is probabilistic and does not generate
    standalone trade signals.
    """

    def __init__(
        self,
        average_range_period: int = 20,
        trend_strength: float = 1.2,
        range_threshold: float = 0.55,
    ) -> None:

        if average_range_period < 2:
            raise ValueError(
                "average_range_period must be >= 2."
            )

        if trend_strength <= 0:
            raise ValueError(
                "trend_strength must be > 0."
            )

        if not 0 < range_threshold < 1:
            raise ValueError(
                "range_threshold must be between 0 and 1."
            )

        self.average_range_period = (
            average_range_period
        )

        self.trend_strength = (
            trend_strength
        )

        self.range_threshold = (
            range_threshold
        )

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
    def _safe_range(
        row: pd.Series,
    ) -> float:

        return max(
            float(row["high"])
            - float(row["low"]),
            1e-12,
        )

    @staticmethod
    def _body(
        row: pd.Series,
    ) -> float:

        return abs(
            float(row["close"])
            - float(row["open"])
        )

    @staticmethod
    def _upper_wick(
        row: pd.Series,
    ) -> float:

        return (
            float(row["high"])
            - max(
                float(row["open"]),
                float(row["close"]),
            )
        )

    @staticmethod
    def _lower_wick(
        row: pd.Series,
    ) -> float:

        return (
            min(
                float(row["open"]),
                float(row["close"]),
            )
            - float(row["low"])
        )

    def _average_range(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.Series:

        ranges = (
            dataframe["high"]
            - dataframe["low"]
        )

        return ranges.rolling(
            self.average_range_period
        ).mean()

    def classify_bars(
        self,
        dataframe: pd.DataFrame,
    ) -> list[BarSignal]:

        self._validate(dataframe)

        average_ranges = (
            self._average_range(
                dataframe
            )
        )

        results: list[BarSignal] = []

        for i in range(
            len(dataframe)
        ):

            row = dataframe.iloc[i]

            candle_range = (
                self._safe_range(row)
            )

            body = self._body(row)

            average_range = (
                average_ranges.iloc[i]
            )

            if pd.isna(
                average_range
            ):
                average_range = candle_range

            body_ratio = (
                body / candle_range
            )

            bullish = (
                float(row["close"])
                > float(row["open"])
            )

            bearish = (
                float(row["close"])
                < float(row["open"])
            )

            if (
                candle_range
                >= average_range
                * self.trend_strength
                and body_ratio >= 0.60
            ):

                bar_type = "trend_bar"

            elif body_ratio <= 0.25:

                bar_type = "doji_or_small_body"

            elif body_ratio >= 0.50:

                bar_type = "strong_body"

            else:

                bar_type = "normal_bar"

            if bullish:
                direction = "bullish"

            elif bearish:
                direction = "bearish"

            else:
                direction = "neutral"

            strength = min(
                1.0,
                body_ratio
                * (
                    candle_range
                    / max(
                        average_range,
                        1e-12,
                    )
                ),
            )

            results.append(
                BarSignal(
                    index=dataframe.index[i],
                    bar_type=bar_type,
                    direction=direction,
                    strength=strength,
                )
            )

        return results

    def detect_signal_bars(
        self,
        dataframe: pd.DataFrame,
    ) -> list[PriceActionPattern]:

        self._validate(dataframe)

        patterns: list[
            PriceActionPattern
        ] = []

        for i in range(
            1,
            len(dataframe),
        ):

            row = dataframe.iloc[i]
            previous = dataframe.iloc[i - 1]

            candle_range = (
                self._safe_range(row)
            )

            body = self._body(row)

            if candle_range <= 0:
                continue

            body_ratio = (
                body / candle_range
            )

            upper_wick = (
                self._upper_wick(row)
            )

            lower_wick = (
                self._lower_wick(row)
            )

            # Bullish signal bar:
            # strong close + meaningful lower rejection.
            bullish_signal = (
                float(row["close"])
                > float(row["open"])
                and body_ratio >= 0.45
                and lower_wick
                > upper_wick
                and float(row["close"])
                > (
                    float(row["low"])
                    + candle_range * 0.60
                )
            )

            if bullish_signal:

                score = min(
                    100.0,
                    50.0
                    + body_ratio * 30.0
                    + min(
                        lower_wick
                        / candle_range,
                        1.0,
                    )
                    * 20.0,
                )

                patterns.append(
                    PriceActionPattern(
                        index=dataframe.index[i],
                        pattern="bullish_signal_bar",
                        direction="bullish",
                        score=score,
                        details={
                            "body_ratio": body_ratio,
                            "lower_wick_ratio":
                                lower_wick
                                / candle_range,
                            "previous_close":
                                float(
                                    previous["close"]
                                ),
                        },
                    )
                )

            # Bearish signal bar:
            # strong close + meaningful upper rejection.
            bearish_signal = (
                float(row["close"])
                < float(row["open"])
                and body_ratio >= 0.45
                and upper_wick
                > lower_wick
                and float(row["close"])
                < (
                    float(row["low"])
                    + candle_range * 0.40
                )
            )

            if bearish_signal:

                score = min(
                    100.0,
                    50.0
                    + body_ratio * 30.0
                    + min(
                        upper_wick
                        / candle_range,
                        1.0,
                    )
                    * 20.0,
                )

                patterns.append(
                    PriceActionPattern(
                        index=dataframe.index[i],
                        pattern="bearish_signal_bar",
                        direction="bearish",
                        score=score,
                        details={
                            "body_ratio": body_ratio,
                            "upper_wick_ratio":
                                upper_wick
                                / candle_range,
                            "previous_close":
                                float(
                                    previous["close"]
                                ),
                        },
                    )
                )

        return patterns

    def detect_breakouts(
        self,
        dataframe: pd.DataFrame,
        lookback: int = 20,
    ) -> list[PriceActionPattern]:

        self._validate(dataframe)

        if lookback < 2:
            raise ValueError(
                "lookback must be >= 2."
            )

        patterns: list[
            PriceActionPattern
        ] = []

        for i in range(
            lookback,
            len(dataframe),
        ):

            row = dataframe.iloc[i]

            previous_high = float(
                dataframe["high"]
                .iloc[
                    i - lookback:i
                ]
                .max()
            )

            previous_low = float(
                dataframe["low"]
                .iloc[
                    i - lookback:i
                ]
                .min()
            )

            close = float(
                row["close"]
            )

            if close > previous_high:

                patterns.append(
                    PriceActionPattern(
                        index=dataframe.index[i],
                        pattern="bullish_breakout",
                        direction="bullish",
                        score=75.0,
                        details={
                            "breakout_level":
                                previous_high,
                            "close": close,
                        },
                    )
                )

            elif close < previous_low:

                patterns.append(
                    PriceActionPattern(
                        index=dataframe.index[i],
                        pattern="bearish_breakout",
                        direction="bearish",
                        score=75.0,
                        details={
                            "breakout_level":
                                previous_low,
                            "close": close,
                        },
                    )
                )

        return patterns

    def detect_failed_breakouts(
        self,
        dataframe: pd.DataFrame,
        lookback: int = 20,
    ) -> list[PriceActionPattern]:

        self._validate(dataframe)

        if lookback < 2:
            raise ValueError(
                "lookback must be >= 2."
            )

        patterns: list[
            PriceActionPattern
        ] = []

        for i in range(
            lookback + 1,
            len(dataframe),
        ):

            previous = dataframe.iloc[i - 1]
            current = dataframe.iloc[i]

            resistance = float(
                dataframe["high"]
                .iloc[
                    i - lookback:i - 1
                ]
                .max()
            )

            support = float(
                dataframe["low"]
                .iloc[
                    i - lookback:i - 1
                ]
                .min()
            )

            previous_close = float(
                previous["close"]
            )

            current_close = float(
                current["close"]
            )

            # Failed upside breakout.
            if (
                float(previous["high"])
                > resistance
                and current_close
                < resistance
            ):

                patterns.append(
                    PriceActionPattern(
                        index=dataframe.index[i],
                        pattern="failed_bullish_breakout",
                        direction="bearish",
                        score=82.0,
                        details={
                            "level": resistance,
                            "breakout_close":
                                previous_close,
                            "failure_close":
                                current_close,
                        },
                    )
                )

            # Failed downside breakout.
            if (
                float(previous["low"])
                < support
                and current_close
                > support
            ):

                patterns.append(
                    PriceActionPattern(
                        index=dataframe.index[i],
                        pattern="failed_bearish_breakout",
                        direction="bullish",
                        score=82.0,
                        details={
                            "level": support,
                            "breakout_close":
                                previous_close,
                            "failure_close":
                                current_close,
                        },
                    )
                )

        return patterns

    def detect_trading_ranges(
        self,
        dataframe: pd.DataFrame,
        window: int = 20,
    ) -> list[PriceActionPattern]:

        self._validate(dataframe)

        if window < 5:
            raise ValueError(
                "window must be >= 5."
            )

        patterns: list[
            PriceActionPattern
        ] = []

        for i in range(
            window,
            len(dataframe) + 1,
        ):

            section = dataframe.iloc[
                i - window:i
            ]

            high = float(
                section["high"].max()
            )

            low = float(
                section["low"].min()
            )

            total_range = (
                high - low
            )

            if total_range <= 0:
                continue

            average_body = (
                (
                    section["close"]
                    - section["open"]
                )
                .abs()
                .mean()
            )

            body_ratio = (
                average_body
                / total_range
            )

            if (
                body_ratio
                <= self.range_threshold
            ):

                index = (
                    dataframe.index[i - 1]
                )

                score = min(
                    100.0,
                    100.0
                    - (
                        body_ratio
                        * 100.0
                    ),
                )

                patterns.append(
                    PriceActionPattern(
                        index=index,
                        pattern="trading_range",
                        direction="neutral",
                        score=score,
                        details={
                            "high": high,
                            "low": low,
                            "range": total_range,
                            "average_body":
                                average_body,
                        },
                    )
                )

        return patterns

    def detect_pullbacks(
        self,
        dataframe: pd.DataFrame,
    ) -> list[PriceActionPattern]:

        self._validate(dataframe)

        patterns: list[
            PriceActionPattern
        ] = []

        if len(dataframe) < 4:
            return patterns

        for i in range(
            2,
            len(dataframe),
        ):

            first = dataframe.iloc[i - 2]
            second = dataframe.iloc[i - 1]
            current = dataframe.iloc[i]

            first_bullish = (
                float(first["close"])
                > float(first["open"])
            )

            second_bearish = (
                float(second["close"])
                < float(second["open"])
            )

            current_bullish = (
                float(current["close"])
                > float(current["open"])
            )

            if (
                first_bullish
                and second_bearish
                and current_bullish
                and float(current["close"])
                > float(first["high"])
            ):

                patterns.append(
                    PriceActionPattern(
                        index=dataframe.index[i],
                        pattern="bullish_pullback",
                        direction="bullish",
                        score=72.0,
                        details={
                            "type":
                                "one_leg_pullback",
                        },
                    )
                )

            first_bearish = (
                float(first["close"])
                < float(first["open"])
            )

            second_bullish = (
                float(second["close"])
                > float(second["open"])
            )

            current_bearish = (
                float(current["close"])
                < float(current["open"])
            )

            if (
                first_bearish
                and second_bullish
                and current_bearish
                and float(current["close"])
                < float(first["low"])
            ):

                patterns.append(
                    PriceActionPattern(
                        index=dataframe.index[i],
                        pattern="bearish_pullback",
                        direction="bearish",
                        score=72.0,
                        details={
                            "type":
                                "one_leg_pullback",
                        },
                    )
                )

        return patterns

    def detect_two_legged_pullbacks(
        self,
        dataframe: pd.DataFrame,
    ) -> list[PriceActionPattern]:

        self._validate(dataframe)

        patterns: list[
            PriceActionPattern
        ] = []

        if len(dataframe) < 5:
            return patterns

        for i in range(
            4,
            len(dataframe),
        ):

            bars = dataframe.iloc[
                i - 4:i + 1
            ]

            directions = []

            for _, row in bars.iterrows():

                if (
                    float(row["close"])
                    > float(row["open"])
                ):
                    directions.append(
                        "bullish"
                    )

                elif (
                    float(row["close"])
                    < float(row["open"])
                ):
                    directions.append(
                        "bearish"
                    )

                else:
                    directions.append(
                        "neutral"
                    )

            bearish_count = (
                directions.count(
                    "bearish"
                )
            )

            bullish_count = (
                directions.count(
                    "bullish"
                )
            )

            if (
                bullish_count >= 3
                and bearish_count >= 2
            ):

                patterns.append(
                    PriceActionPattern(
                        index=dataframe.index[i],
                        pattern="possible_two_legged_bull_pullback",
                        direction="bullish",
                        score=65.0,
                        details={
                            "bars":
                                directions,
                        },
                    )
                )

            elif (
                bearish_count >= 3
                and bullish_count >= 2
            ):

                patterns.append(
                    PriceActionPattern(
                        index=dataframe.index[i],
                        pattern="possible_two_legged_bear_pullback",
                        direction="bearish",
                        score=65.0,
                        details={
                            "bars":
                                directions,
                        },
                    )
                )

        return patterns

    def detect_high_low_123(
        self,
        dataframe: pd.DataFrame,
    ) -> list[PriceActionPattern]:

        self._validate(dataframe)

        patterns: list[
            PriceActionPattern
        ] = []

        if len(dataframe) < 3:
            return patterns

        for i in range(
            2,
            len(dataframe),
        ):

            first = dataframe.iloc[i - 2]
            second = dataframe.iloc[i - 1]
            third = dataframe.iloc[i]

            # Bullish 1-2-3.
            bullish = (
                float(first["low"])
                < float(second["low"])
                and float(second["low"])
                < float(third["low"])
                and float(third["close"])
                > float(second["high"])
            )

            if bullish:

                patterns.append(
                    PriceActionPattern(
                        index=dataframe.index[i],
                        pattern="bullish_123",
                        direction="bullish",
                        score=70.0,
                        details={
                            "type":
                                "high_low_123",
                        },
                    )
                )

            # Bearish 1-2-3.
            bearish = (
                float(first["high"])
                > float(second["high"])
                and float(second["high"])
                > float(third["high"])
                and float(third["close"])
                < float(second["low"])
            )

            if bearish:

                patterns.append(
                    PriceActionPattern(
                        index=dataframe.index[i],
                        pattern="bearish_123",
                        direction="bearish",
                        score=70.0,
                        details={
                            "type":
                                "high_low_123",
                        },
                    )
                )

        return patterns

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        self._validate(dataframe)

        bars = self.classify_bars(
            dataframe
        )

        signal_bars = (
            self.detect_signal_bars(
                dataframe
            )
        )

        breakouts = (
            self.detect_breakouts(
                dataframe
            )
        )

        failed_breakouts = (
            self.detect_failed_breakouts(
                dataframe
            )
        )

        ranges = (
            self.detect_trading_ranges(
                dataframe
            )
        )

        pullbacks = (
            self.detect_pullbacks(
                dataframe
            )
        )

        two_legged = (
            self.detect_two_legged_pullbacks(
                dataframe
            )
        )

        patterns_123 = (
            self.detect_high_low_123(
                dataframe
            )
        )

        patterns = (
            signal_bars
            + breakouts
            + failed_breakouts
            + ranges
            + pullbacks
            + two_legged
            + patterns_123
        )

        bullish_score = sum(
            pattern.score
            for pattern in patterns
            if pattern.direction
            == "bullish"
        )

        bearish_score = sum(
            pattern.score
            for pattern in patterns
            if pattern.direction
            == "bearish"
        )

        if bullish_score > bearish_score:
            bias = "bullish"

        elif bearish_score > bullish_score:
            bias = "bearish"

        else:
            bias = "neutral"

        return {
            "bias": bias,
            "bullish_score": round(
                bullish_score,
                2,
            ),
            "bearish_score": round(
                bearish_score,
                2,
            ),
            "bars": bars,
            "signal_bars": signal_bars,
            "breakouts": breakouts,
            "failed_breakouts":
                failed_breakouts,
            "trading_ranges": ranges,
            "pullbacks": pullbacks,
            "two_legged_pullbacks":
                two_legged,
            "high_low_123":
                patterns_123,
            "patterns": patterns,
        }
